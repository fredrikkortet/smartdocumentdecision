import json
import os
import shutil
import tempfile
import logging
from typing import Any, Optional

import json
import os
import shutil
import tempfile
import logging
from typing import Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette import status

from main import process_document
from ai.backend.stub_backend import StubBackend
from ai.backend.llm_ollama import OllamaBackend
from ai.backend.llm_hf import HFBackend
from ai.schema import BackendSpec # Import the new schema


logger = logging.getLogger("smartdoc_api")
if not logger.handlers:
    # Basic console logging configuration
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _load_backend(link: BackendSpec | None) -> Any:
    """Pick the full LLM backend using the provided options.

    link may look like:
      BackendSpec(provider="ollama", model="gemma3")
      BackendSpec(provider="hf", model="mistralai/Mistral-7B-Instruct-v0.2")

    If link is None or provider not known, return None (use default in main.process_document).
    """
    if not link:
        return None
    p = str(link.provider).lower()
    model = link.model
    try:
        if p == "ollama":
            return OllamaBackend(model=model or "gemma3")
        if p in ("hf", "huggingface"):
            return HFBackend(model_name=model or "mistralai/Mistral-7B-Instruct-v0.2")
    except Exception as e:
        logger.exception("Failed to initialize backend: %s", e)
        return None
    return None


app = FastAPI(title="AI Document Relevance Agent")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Incoming request: %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
        logger.info("Completed request: %s %s -> %s", request.method, request.url.path, response.status_code)
        return response
    except Exception as e:
        logger.exception("Unhandled error during request")
        raise


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP error for %s %s -> %s", request.method, request.url.path, exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"type": "http", "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error for %s %s -> %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"type": "validation", "message": "Invalid request", "details": exc.errors()}},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"type": "internal", "message": "Internal server error"}},
    )


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    use_stub: Optional[bool] = Form(False),
    backend_spec: Optional[str] = Form(None),
):
    logger.info("Analyze called: filename=%s use_stub=%s", getattr(file, "filename", None), use_stub)

    # Save uploaded file to a temporary file
    try:
        suffix = os.path.splitext(file.filename or "")[1] or ".txt"
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        with tmp_file as f:
            shutil.copyfileobj(file.file, f)
        file_path = tmp_file.name
        logger.debug("Saved uploaded file to %s", file_path)
    except Exception as e:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=400, detail=f"Failed to save uploaded file: {e}")

    # Save context if provided
    ctx_path = None
    if context:
        try:
            tmp_ctx = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
            with tmp_ctx as f:
                f.write(context.encode("utf-8"))
            ctx_path = tmp_ctx.name
            logger.debug("Saved context to %s", ctx_path)
        except Exception as e:
            logger.exception("Failed to save context file")
            try:
                os.unlink(file_path)
            except Exception:
                pass
            raise HTTPException(status_code=400, detail=f"Failed to save context: {e}")

    # Choose backend
    backend = None
    if use_stub:
        # Return simple stub responses; keep them generic
        backend = StubBackend(
            responses={
                "Summarize the following text chunk": json.dumps({
                    "summary": "Stub chunk summary",
                    "topics": ["test"],
                    "confidence": 0.9,
                }),
                "Extract the most important information": json.dumps({
                    "entities": ["test"],
                    "facts": ["fact1"],
                    "numbers": [],
                    "actions": [],
                    "misc": [],
                }),
                "Combine all chunk information": json.dumps({
                    "summary": "Stub combined summary",
                    "insights": ["insight1"],
                    "uncertainties": [],
                    "confidence": 0.8,
                }),
            }
        )
        logger.info("Using StubBackend for analysis")

    # If a backend spec JSON is provided via backend_spec (e.g. {"provider":"ollama","model":"gemma3"}), parse and load backend
    try:
        backend_options = None
        if backend is None and backend_spec:
            try:
                # Use Pydantic to validate the JSON string
                backend_options = BackendSpec.model_validate_json(backend_spec)
                backend = _load_backend(backend_options)
                logger.info("Loaded backend from spec: %s", backend_options.model_dump())
            except Exception as e:
                logger.warning("Failed to parse or validate backend_spec: %s", e)
                raise HTTPException(status_code=400, detail=f"Invalid backend_spec format: {e}")

        logger.info("Processing document %s with backend=%s", file_path, type(backend).__name__ if backend else None)
        result = process_document(file_path, ctx_path or "context.md", backend=backend)
        logger.info("Processing complete for %s", file_path)
    except HTTPException:
        # Re-raise HTTPExceptions to be handled by FastAPI
        raise
    except Exception as e:
        logger.exception("Error while processing document")
        # Cleanup temp files
        try:
            os.unlink(file_path)
        except Exception:
            pass
        if ctx_path:
            try:
                os.unlink(ctx_path)
            except Exception:
                pass
        # Raise a generic HTTPException which will be formatted by our handlers
        raise HTTPException(status_code=500, detail=str(e))

    # Cleanup temp files
    try:
        os.unlink(file_path)
    except Exception:
        pass
    if ctx_path:
        try:
            os.unlink(ctx_path)
        except Exception:
            pass

    return JSONResponse(content=result)

