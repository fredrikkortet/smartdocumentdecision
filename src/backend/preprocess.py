import re
from typing import List


def remove_headers_footers(text: str, repeated_threshold=2) -> str:
    """
    Remove lines that appear multiple times (likely headers/footers)
    """
    lines = text.splitlines()
    line_counts = {}
    for line in lines:
        line_counts[line] = line_counts.get(line, 0) + 1
    clean_lines = [line for line in lines if line_counts[line] < repeated_threshold]
    return "\n".join(clean_lines)


def normalize_text(text: str) -> str:
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
    text = remove_headers_footers(text)
    text = normalize_text(text)
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
    return chunks


# Example usage
if __name__ == "__main__":
    sample_text = "This  is    some text.\n\n\n\tWith inconsistent  spacing.\r\nAnother line."
    clean_text = preprocess_text(sample_text)
    print(clean_text)
