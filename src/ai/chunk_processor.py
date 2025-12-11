import json
import re
from pathlib import Path
from ai.backend.llm_ollama import OllamaBackend
from ai.schema import ChunkResult


class ChunkProcessor:
    def __init__(self, backend=None):
        self.llm = backend or OllamaBackend(model="gemma3")

        base = Path(__file__).parent / "prompts"
        self.summary_template = (base / "chunk_summary.txt").read_text()
        self.keyinfo_template = (base / "chunk_keyinfo.txt").read_text()

    def fill(self, template: str, chunk: str) -> str:
        return template.replace("{{chunk_text}}", chunk)

    def _parse_json_if_possible(self, text: str):
        cleaned = self.safe_parse_llm_output(text)
        try:
            return json.loads(cleaned)
        except Exception:
            return None

    def process_chunk(self, chunk_text: str, chunk_id: int) -> ChunkResult:
        summary_prompt = self.fill(self.summary_template, chunk_text)
        key_prompt = self.fill(self.keyinfo_template, chunk_text)

        # Get raw outputs
        summary_raw = self.llm.chat(summary_prompt)
        key_info_raw = self.llm.chat(key_prompt)

        # Parse key info into structured dict if possible
        key_info_clean = self.safe_parse_llm_output(key_info_raw)
        try:
            key_info = json.loads(key_info_clean)
        except json.JSONDecodeError:
            key_info = {"error": "INVALID_JSON", "raw": key_info_clean}

        # Try to parse summary if it is a JSON blob (some LLMs may return structured summaries)
        summary_parsed = self._parse_json_if_possible(summary_raw)
        if isinstance(summary_parsed, dict):
            summary_text = summary_parsed.get("summary", str(summary_parsed))
            summary_topics = summary_parsed.get("topics", [])
        else:
            summary_text = summary_raw
            summary_topics = []

        # Build topics list from key_info 'entities' and summary topics
        topics = []
        if isinstance(key_info, dict):
            entities = key_info.get("entities") or key_info.get("entities", [])
            if isinstance(entities, list):
                topics.extend([str(e) for e in entities])
            # If 'facts' contain named things, include them as topics
            facts = key_info.get("facts", [])
            if isinstance(facts, list):
                # heuristic: take first noun-like word; keep simple and just include facts
                topics.extend([str(f) for f in facts])

        if isinstance(summary_topics, list):
            topics.extend([str(t) for t in summary_topics])

        # dedupe topics
        topics = list({t for t in topics})

        return ChunkResult(chunk_id=chunk_id, text=chunk_text, summary=summary_text, key_info=key_info, topics=topics)

    def safe_parse_llm_output(self, text):
        # 0. Remove ```json ... ``` wrappers if present
        cleaned = re.sub(r"```json\s*|\s*```", "", text, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        return cleaned
