import json
import os
import tempfile
import traceback

import streamlit as st

from main import process_document
from ai.backend.stub_backend import StubBackend

try:
    from ai.backend.llm_ollama import OllamaBackend
except Exception:
    OllamaBackend = None

try:
    from ai.backend.llm_hf import HFBackend
except Exception:
    HFBackend = None


def _load_backend(link: dict | None):
    if not link:
        return None
    p = str(link.get("provider", "")).lower()
    model = link.get("model")
    try:
        if p == "ollama" and OllamaBackend:
            return OllamaBackend(model=model or "gemma3")
        if p in ("hf", "huggingface") and HFBackend:
            return HFBackend(model_name=model or "mistralai/Mistral-7B-Instruct-v0.2")
    except Exception:
        return None
    return None


st.set_page_config(page_title="AI Document Relevance Agent", layout="centered")
st.title("AI Document Relevance Agent — Streamlit UI")

st.markdown("Upload a document, optionally edit the agent context, and click Analyze.")

uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"], accept_multiple_files=False)
context_md = st.text_area("Edit context.md (agent behavior configuration)", height=200)
use_stub = st.checkbox("Use Stub Backend (fast, local)", value=False)
backend_spec_input = st.text_input('Backend spec JSON (optional, e.g. {"provider":"ollama","model":"gemma3"})')

if st.button("Analyze"):
    if not uploaded_file:
        st.error("Please upload a file to analyze.")
    else:
        tmp_file = None
        tmp_ctx = None
        try:
            suffix = os.path.splitext(uploaded_file.name)[1] or ".txt"
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(uploaded_file.getbuffer())
            tmp_file = tmp_path

            if context_md and context_md.strip():
                tmp_ctx_fd, tmp_ctx_path = tempfile.mkstemp(suffix=".md")
                with os.fdopen(tmp_ctx_fd, "w", encoding="utf-8") as f:
                    f.write(context_md)
                tmp_ctx = tmp_ctx_path

            backend = None
            if use_stub:
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

            if backend_spec_input and not use_stub:
                try:
                    spec = json.loads(backend_spec_input)
                except Exception:
                    st.warning("Failed to parse backend_spec JSON; ignoring and using default backend.")
                    spec = None
                if spec:
                    backend = _load_backend(spec)
                    if backend is None:
                        st.warning("Requested backend could not be initialized; continuing without backend.")

            with st.spinner("Analyzing document..."):
                result = process_document(tmp_file, tmp_ctx or "context.md", backend=backend)

            st.success("Analysis complete")

            # Display structured results if present
            try:
                st.subheader("Summary")
                if isinstance(result, dict) and result.get("summary"):
                    st.write(result.get("summary"))
                else:
                    st.write("No summary field; showing raw result below.")

                st.subheader("Key Insights / Key Info")
                if isinstance(result, dict) and result.get("insights"):
                    st.write(result.get("insights"))
                elif isinstance(result, dict) and result.get("key_info"):
                    st.write(result.get("key_info"))
                else:
                    st.write("No key insights field; see raw result.")

                st.subheader("uncertainties")
                if isinstance(result, dict) and result.get("uncertainties"):
                    st.write(result.get("uncertainties"))
                else:
                    st.write("")

                st.subheader("Recommendation")
                if isinstance(result, dict) and result.get("recommendation"):
                    st.write(result.get("recommendation"))
                else:
                    st.write("No recommendation field; see raw result.")

                st.subheader("Need full read")
                if isinstance(result, dict) and result.get("need_full_read"):
                    st.write(result.get("need_full_read"))
                else:
                    st.write("")

                st.subheader("Read Reasoning")
                if isinstance(result, dict) and result.get("read_reasons"):
                    st.write(result.get("read_reasons"))
                else:
                    st.write("")

                st.subheader("Raw JSON Result")
                st.json(result)
            except Exception:
                st.error("Failed to render result: " + traceback.format_exc())

            # Offer context download
            if context_md and context_md.strip():
                st.download_button("Download context.md", data=context_md, file_name="context.md")

        except Exception as e:
            st.error(f"Error during analysis: {e}\n{traceback.format_exc()}")
        finally:
            try:
                if tmp_file and os.path.exists(tmp_file):
                    os.unlink(tmp_file)
                if tmp_ctx and os.path.exists(tmp_ctx):
                    os.unlink(tmp_ctx)
            except Exception:
                pass

st.markdown("---")
st.write("Tip: Run the Streamlit app with `streamlit run src/frontend/streamlit_app.py` and ensure the project's dependencies are installed.")
