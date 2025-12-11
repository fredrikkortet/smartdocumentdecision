import json
from pathlib import Path

from ai.backend.stub_backend import StubBackend
from ai.context_loader import ContextLoader
from ai.chunk_processor import ChunkProcessor
from ai.document_reasoner import DocumentReasoner
from ai.decision_engine import DecisionEngine
from ai.schema import ChunkResult
from document_processing.processor import preprocess_text, chunk_text
from storage.jsonl_store import JSONLStore


def test_preprocess_and_chunk():
    sample_path = Path("tests/documents/sample.txt")
    raw = sample_path.read_text(encoding="utf-8")

    cleaned = preprocess_text(raw)
    assert "  " not in cleaned  # no double spaces
    assert "\t" not in cleaned

    chunks = chunk_text(cleaned, chunk_size=200, overlap=40)
    assert isinstance(chunks, list)
    assert len(chunks) >= 2


def test_context_loader_parsing():
    ctx = ContextLoader("context.md").load_parsed()
    assert isinstance(ctx, dict)
    assert "priority_topics" in ctx and isinstance(ctx["priority_topics"], list)
    assert any(t.lower().strip() == "legal" for t in ctx["priority_topics"])  # focus=legal
    assert ctx.get("sensitivity") is not None


def test_chunk_processor_parses_json_and_topics():
    # Stub responses tuned to match prompt snippets
    stub = StubBackend(
        responses={
            "Summarize the following text chunk": json.dumps({
                "summary": "Chunk summary",
                "topics": ["legal", "finance"],
                "confidence": 0.9,
            }),
            "Extract the most important information": json.dumps({
                "entities": ["legal", "finance"],
                "facts": ["fact1"],
                "numbers": [],
                "actions": [],
                "misc": [],
            }),
        }
    )

    processor = ChunkProcessor(backend=stub)
    chunk_text_input = "This is a test chunk that includes legal and finance topics."
    result = processor.process_chunk(chunk_text_input, 0)

    # result may be pydantic model or dataclass
    # prefer model_dump when available, otherwise fallback to dict
    # prefer model_dump when available, otherwise fallback to dict
    if hasattr(result, 'model_dump'):
        try:
            d = result.model_dump()
        except Exception:
            d = result.dict() if hasattr(result, 'dict') else result
    elif hasattr(result, 'dict'):
        d = result.dict()
    else:
        d = result
    assert isinstance(d["summary"], str)
    assert isinstance(d["key_info"], dict)
    assert "entities" in d["key_info"]
    assert "legal" in d["topics"]


def test_document_reasoner_combine_returns_parsed_json():
    stub = StubBackend(
        responses={
            "Combine all chunk information": json.dumps({
                "summary": "Combined summary",
                "insights": ["i1"],
                "uncertainties": [],
                "confidence": 0.75,
            })
        }
    )

    # prepare chunk results: simple dicts are fine
    chunk_results = [
        {"chunk_id": 0, "summary": "s1", "key_info": {}, "topics": ["legal"]},
    ]

    reasoner = DocumentReasoner(stub, context_path="context.md")
    combined = reasoner.combine(chunk_results)
    assert isinstance(combined, dict)
    assert combined["summary"] == "Combined summary"
    assert isinstance(combined["insights"], list)


def test_decision_engine_scoring():
    ctx = ContextLoader("context.md").load_parsed()
    engine = DecisionEngine(context_rules=ctx)

    combined = {"combined_topics": ["legal", "finance"]}
    score = engine.compute_read_worthiness(combined)
    assert 0.0 <= score <= 1.0
    # high sensitivity + two priority topics should give a high score
    assert score > 0.6


def test_process_document_end_to_end(tmp_path):
    # Use StubBackend to avoid external LLM interactions
    stub = StubBackend(
        responses={
            "Summarize the following text chunk": json.dumps({"summary": "Chunk summary", "topics": ["legal"], "confidence": 0.9}),
            "Extract the most important information": json.dumps({"entities": ["legal"], "facts": ["f1"], "numbers": [], "actions": [], "misc": []}),
            "Combine all chunk information": json.dumps({"summary": "Combined summary", "insights": ["i1"], "uncertainties": [], "confidence": 0.7}),
        }
    )

    from main import process_document

    result = process_document(str(Path("tests/documents/sample.txt")), "context.md", backend=stub)
    assert isinstance(result, dict)
    assert "summary" in result
    assert "topics" in result
    assert isinstance(result["chunks"], list)


def test_jsonl_store_save_load(tmp_path):
    store_path = tmp_path / "chunks.jsonl"
    store = JSONLStore(str(store_path))
    cr = ChunkResult(chunk_id=1, text="t", summary="s", key_info={"entities":["a"]}, topics=["a"]) if hasattr(ChunkResult, "model_dump") or hasattr(ChunkResult, "dict") else None

    # Create a fallback plain dict if ChunkResult cannot be instantiated
    if cr is None:
        cr = {"chunk_id": 1, "text": "t", "summary": "s", "key_info": {"entities": ["a"]}, "topics": ["a"]}

    store.save_chunk(cr)
    loaded = store.load_all()
    assert len(loaded) >= 1
    assert loaded[0].chunk_id == 1
