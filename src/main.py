import json
import pathlib

from document_processing.processor import extract_text, preprocess_text, chunk_text
from ai.document_reasoner import DocumentReasoner
from ai.backend.llm_ollama import OllamaBackend
from ai.chunk_processor import ChunkProcessor
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


if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 2:
        print("Usage: python main.py <document_path>")
        sys.exit(1)

    doc_path = sys.argv[1]
    main(doc_path, sys.argv[2])
