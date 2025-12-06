import os

import pdfplumber

try:
    import pytresseract

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

import docx
import re
from typing import List


def _extract_text_from_pdf(pdf_path: str, use_ocr=False) -> str:
    """
    Extract full text from a PDF.

    args:
        pdf_path: path to the PDF file
        use_ocr: Whether to use OCR fro scanned PDFs

    Returns:
        Full text as a single string
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            elif use_ocr and OCR_AVAILABLE:
                # fallback OCR
                pil_image = page.to_image(resolution=300).original
                page_text = pytresseract.image_to_string(pil_image)
                text += page_text + "\n"
            else:
                text += "\n"
    return text


def _extract_text_from_docx(docx_path: str) -> str:
    doc = docx.Document(docx_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)


def _extract_text_from_txt(txt_path: str) -> str:
    with open(txt_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text(file_path: str, use_ocr=False) -> str:
    """
    Unified document extractor.

    Args:
        file_path: Path to document (PDF, DOCX, TXT)
        use_ocr: use OCR for scanned PDFs

    Returns:
        Full extracted text as a string
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_text_from_pdf(file_path, use_ocr=use_ocr)
    elif ext == ".docx":
        return _extract_text_from_docx(file_path)
    elif ext == ".txt":
        return _extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _remove_headers_footers(text: str, repeated_threshold=2) -> str:
    """
    Remove lines that appear on multiple pages (likely headers/footers).
    """
    lines = text.splitlines()
    line_counts = {}
    for line in lines:
        line_counts[line] = line_counts.get(line, 0) + 1
    clean_lines = [line for line in lines if line_counts[line] < repeated_threshold]
    return "\n".join(clean_lines)


def _normalize_text(text: str) -> str:
    """
    Normalize whitespace and line breaks in text.

    - Replace multiple spaces/tabs with a single space
    - Remove leading/trailing spaces on each line
    - Normalize line breaks to '\n'
    - Remove excessive consecutive line breaks
    """
    # Replace tabs with space
    text = text.replace("\t", " ")

    # Remove multiple spaces
    text = re.sub(r" +", " ", text)

    # Normalize line breaks to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove leading/trailing spaces on each line
    lines = [line.strip() for line in text.split("\n")]

    # Remove empty lines at start/end
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()

    # Reduce consecutive empty lines to a maximum of 1
    normalized_lines = []
    previous_line_empty = False
    for line in lines:
        if line == "":
            if not previous_line_empty:
                normalized_lines.append(line)
            previous_line_empty = True
        else:
            normalized_lines.append(line)
            previous_line_empty = False

    normalized_text = "\n".join(normalized_lines)
    return normalized_text


def preprocess_text(text: str) -> str:
    """
    Full preprocessing pipeline:
    1. Remove headers/footers
    2. Normalize whitespace and line breaks
    """
    text = _remove_headers_footers(text)
    text = _normalize_text(text)
    return text


def chunk_text(text: str, chunk_size=2000, overlap=200) -> List[dict]:
    """
    Split text into overlapping chunks.
    """
    chunks = []
    start = 0
    text_len = len(text)
    chunk_id = 0
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append({"chunk_id": chunk_id, "text": text[start:end]})
        chunk_id += 1
        start = end - overlap
        if end == text_len:
            break
    return chunks


# Example usage
if __name__ == "__main__":
    sample_text = "This  is    some text.\n\n\n\tWith inconsistent  spacing.\r\nAnother line."
    clean_text = preprocess_text(sample_text)
    print(clean_text)

    pdf_file = "sample.pdf"
    extracted_text = extract_text(pdf_file, use_ocr=True)
    cleaned_text = _remove_headers_footers(extracted_text)
    print(cleaned_text[:500])  # print first 500 characters
