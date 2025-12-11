import json
import pathlib

from document_processing.processor import extract_text, preprocess_text, chunk_text
from ai.document_reasoner import DocumentReasoner
from ai.decision_engine import DecisionEngine
from ai.backend.llm_ollama import OllamaBackend
from ai.chunk_processor import ChunkProcessor
from ai.context_loader import ContextLoader
from storage.jsonl_store import JSONLStore


def main(file_path: str, context_path: str = "context.md"):
    # Extract and clean text
    raw_text = extract_text(file_path, use_ocr=True)
    clean_text = preprocess_text(raw_text)

    # Split sections into chunks (simple example: by 1000 chars)
    chunks = []
    chunk_size = 100
    overlap = 20
    chunks = chunk_text(text=clean_text, chunk_size=chunk_size, overlap=overlap)

    llm_client = OllamaBackend(model="gemma3")

    #  Process chunks with LLM
    processor = ChunkProcessor(llm_client)
    chunk_results = []
    for idx, chunk in enumerate(chunks):
        chunk_result = processor.process_chunk(chunk["text"], idx)
        chunk_results.append(chunk_result)

    #  Store chunk results
    store = JSONLStore("output/chunks.jsonl")
    store.save_many(chunk_results)

    reasoner = DocumentReasoner(llm_client, context_path=context_path)
    final_result = reasoner.combine(chunk_results)

    # Save results
    output_dir = pathlib.Path("output")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "document_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_result, f, indent=2)

    print(f"Processed {len(chunks)} chunks and stored results at output/chunks.jsonl and document_analysis.json")


def process_document(file_path: str, context_path: str, backend=None):
    # -------------------------
    # 1. Load context.md rules (as parsed dict)
    # -------------------------
    context_parsed = ContextLoader(context_path).load_parsed()

    # -------------------------
    # 2. Extract, chunk and analyze
    # -------------------------
    raw_text = extract_text(file_path, use_ocr=True)
    clean_text = preprocess_text(raw_text)
    chunks = chunk_text(clean_text, chunk_size=1000, overlap=200)

    ai = backend or OllamaBackend(model="gemma3")
    processor = ChunkProcessor(ai)

    chunk_summaries = []
    for c in chunks:
        analysis = processor.process_chunk(c["text"], c["chunk_id"])
        if hasattr(analysis, "model_dump"):
            chunk_summaries.append(analysis.model_dump())
        elif hasattr(analysis, "dict"):
            chunk_summaries.append(analysis.dict())
        else:
            chunk_summaries.append(analysis)

    # metadata (expand later if needed)
    metadata = {
        "file_path": file_path,
        "chunk_count": len(chunks),
        "ocr_used": False,  # set to True if OCR triggered
    }

    # -------------------------
    # 3. Decision Engine
    # -------------------------
    engine = DecisionEngine(context_rules=context_parsed)

    combined = engine.combine_responses(chunk_summaries, metadata)
    score = engine.compute_read_worthiness(combined)
    confidence = engine.compute_confidence(chunk_summaries, metadata)
    recommendation = engine.final_recommendation(score)

    # Additional document-level run via DocumentReasoner to extract insights/uncertainties
    reasoner = DocumentReasoner(ai, context_path=context_path)
    try:
        doc_level = reasoner.combine(chunk_summaries)
    except Exception:
        doc_level = {"summary": combined["combined_summary"], "insights": [], "uncertainties": [], "confidence": 0.0}

    # Decision details from the reasoner
    decision_details = reasoner.decide_need_full_read(doc_level)

    # -------------------------
    # 4. Final Output
    # -------------------------
    return {
        "summary": combined["combined_summary"],
        "doc_summary": doc_level.get("summary", combined["combined_summary"]),
        "insights": doc_level.get("insights", []),
        "uncertainties": doc_level.get("uncertainties", []),
        "doc_confidence": doc_level.get("confidence", 0.0),
        "topics": combined["combined_topics"],
        "score": score,
        "recommendation": recommendation,
        "need_full_read": decision_details.get("need_full_read", False),
        "read_reasons": decision_details.get("reasons", []),
        "confidence": confidence,
        "metadata": metadata,
        "chunks": chunk_summaries,
        "context": context_parsed,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "ui":
        import subprocess
        import os
        
        # Ensure PYTHONPATH includes the src directory
        src_path = str(pathlib.Path(__file__).parent.absolute())
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{src_path}:{current_pythonpath}" if current_pythonpath else src_path
        
        # Determine the path to the streamlit app
        app_path = pathlib.Path(__file__).parent / "frontend" / "streamlit_app.py"
        
        print(f"Launching Streamlit UI from {app_path}...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], env=env)
        sys.exit(0)

    if len(sys.argv) <= 2:
        print("Usage: ")
        print("  Run UI:  python src/main.py ui")
        print("  Run CLI: python src/main.py <document_path> <context_path>")
        sys.exit(1)

    doc_path = sys.argv[1]
    # main(doc_path, sys.argv[2])
    process_document(doc_path, sys.argv[2])
