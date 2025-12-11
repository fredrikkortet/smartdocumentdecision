from fastapi.testclient import TestClient
from pathlib import Path

from api.app import app

client = TestClient(app)


def test_analyze_with_stub_file():
    file_path = Path("tests/documents/sample.txt")
    with file_path.open("rb") as f:
        files = {"file": ("sample.txt", f, "text/plain")}
        data = {"use_stub": "true"}
        r = client.post("/analyze", data=data, files=files)

    assert r.status_code == 200
    payload = r.json()
    assert "summary" in payload
    assert "topics" in payload
    assert "chunks" in payload and isinstance(payload["chunks"], list)
    assert "score" in payload
    assert "recommendation" in payload


def test_analyze_with_context_and_stub():
    file_path = Path("tests/documents/sample.txt")
    ctx = "focus=marketing\nsensitivity=low"
    with file_path.open("rb") as f:
        files = {"file": ("sample.txt", f, "text/plain")}
        data = {"use_stub": "true", "context": ctx}
        r = client.post("/analyze", data=data, files=files)

    assert r.status_code == 200
    payload = r.json()
    assert "context" in payload
    ctx_parsed = payload["context"]
    # focus -> priority_topics
    assert any("marketing" in (t or "").lower() for t in ctx_parsed.get("priority_topics", []))


def test_analyze_with_valid_backend_spec():
    file_path = Path("tests/documents/sample.txt")
    backend_spec = '{"provider": "ollama", "model": "gemma3"}'
    with file_path.open("rb") as f:
        files = {"file": ("sample.txt", f, "text/plain")}
        data = {"backend_spec": backend_spec}
        r = client.post("/analyze", data=data, files=files)

    # Since we are not mocking the actual Ollama backend, this test primarily checks
    # that the API accepts the input without a 400 error due to validation.
    # It will likely fail with 500 if Ollama is not running, but 200 means validation passed.
    # We assert for 200 or 500, but not 400.
    assert r.status_code in (200, 500)
    if r.status_code == 500:
        # Check for a specific error message related to backend failure
        assert "error" in r.json()
        assert "Failed to initialize backend" in r.json()["error"]["message"] or "Error while processing document" in r.json()["error"]["message"]


def test_analyze_with_invalid_backend_spec():
    file_path = Path("tests/documents/sample.txt")
    # Invalid JSON
    backend_spec_invalid_json = '{"provider": "ollama", "model": "gemma3"'
    with file_path.open("rb") as f:
        files = {"file": ("sample.txt", f, "text/plain")}
        data = {"backend_spec": backend_spec_invalid_json}
        r = client.post("/analyze", data=data, files=files)

    assert r.status_code == 400
    assert "Invalid backend_spec format" in r.json()["error"]["message"]

    # Invalid schema (missing required field 'model')
    backend_spec_invalid_schema = '{"provider": "ollama"}'
    with file_path.open("rb") as f:
        files = {"file": ("sample.txt", f, "text/plain")}
        data = {"backend_spec": backend_spec_invalid_schema}
        r = client.post("/analyze", data=data, files=files)

    assert r.status_code == 400
    assert "Invalid backend_spec format" in r.json()["error"]["message"]


def test_analyze_unsupported_extension_returns_500():
    file_path = Path("tests/documents/sample.txt")
    with file_path.open("rb") as f:
        files = {"file": ("sample.abc", f, "application/octet-stream")}
        data = {"use_stub": "true"}
        r = client.post("/analyze", data=data, files=files)

    assert r.status_code == 500
    payload = r.json()
    assert "error" in payload
    assert "Unsupported file type: .abc" in payload["error"]["message"]
