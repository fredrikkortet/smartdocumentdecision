from document_processing.processor import extract_text, preprocess_text, chunk_text
from ai.chunk_processor import ChunkProcessor
from storage.jsonl_store import JSONLStore

def main(file_path: str):
    # Extract and clean text
    raw_text = extract_text(file_path, use_ocr=True)
    clean_text = preprocess_text(raw_text)
    
    # Split sections into chunks (simple example: by 1000 chars)
    chunks = []
    chunk_size = 1000
    overlap = 200
    chunks = chunk_text(text=clean_text, chunk_size=chunk_size, overlap=overlap)

    #  Process chunks with LLM
    processor = ChunkProcessor()
    results = []
    for idx, chunk in enumerate(chunks):
        result = processor.process_chunk(chunk, idx)
        results.append(result)

    #  Store results
    store = JSONLStore("output/chunks.jsonl")
    store.save_many(results)

    print(f"Processed {len(chunks)} chunks and stored results at output/chunks.jsonl")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python main.py <document_path>")
        sys.exit(1)

    doc_path = sys.argv[1]
    main(doc_path)

