def combine_chunks_prompt(chunk_summaries, chunk_key_info, context_notes=""):
    return f"""
You are an AI that performs high-level reasoning over document fragments.

## Chunk Summaries
{chunk_summaries}

## Extracted Key Information
{chunk_key_info}

## Context Notes (optional)
{context_notes}

### Task
Combine all chunk information into a single unified document understanding.
Provide:
1. A coherent document summary (200 words max)
2. A bullet list of the most important insights
3. Any contradictions or unclear sections
4. A confidence score (0–1)

Return valid JSON with the following structure:
Do NOT include:
- Backticks
- ```json
- Code blocks
- Explanations

{{
    "summary": "...",
    "insights": ["...", "..."],
    "uncertainties": ["...", "..."],
    "confidence": 0.0
}}
"""
