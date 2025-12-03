import os 

import pdfplumber
from typing import Optional
try:
    import pytresseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

import docx


def extract_text_from_pdf(pdf_path: str, use_ocr=False) -> str:
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


def extract_text_from_docx(docx_path: str) -> str:
    doc = docx.Document(docx_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)


def extract_text_from_txt(txt_path: str) -> str:
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
    ext = os.path.splittext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path, use_ocr=use_ocr)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def remove_headers_footers(text: str, repeated_threshold=2) -> str:
    """
    Remove lines that appear on multiple pages (likely headers/footers).
    """
    lines = text.splitlines()
    line_counts = {}
    for line in lines:
        line_counts[line] = line_counts.get(line, 0) + 1
    clean_lines = [line for line in lines if line_counts[line] < repeated_threshold]
    return "\n".join(clean_lines)


if __name__ == "__main__":
    pdf_file = "sample.pdf"
    extracted_text = extract_text(pdf_file, use_ocr=True)
    cleaned_text = remove_headers_footers(extracted_text)
    print(cleaned_text[:500]) # print first 500 characters
