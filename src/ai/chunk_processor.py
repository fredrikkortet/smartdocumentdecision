import json
from pathlib import Path
from ai.backend.llm_base import LLMResponse
from ai.backend.llm_ollama import OllamaBackend
from ai.schema import ChunkResult

class ChunkProcessor:

    def __init__(self, backend=None):
        self.llm = backend or OllamaBackend(model="mistral")

        base = Path(__file__).parent / "prompts"
        self.summary_template = (base / "chunk_summary.txt").read_text()
        self.keyinfo_template = (base / "chunk_keyinfo.txt").read_text()

    def fill(self, template: str, chunk: str) -> str:
        return template.replace("{{chunk_text}}", chunk)


    def process_chunk(self, chunk_text: str, chunk_id: int) -> ChunkResult:
        summary_prompt = self.fill(self.summary_template, chunk_text)
        key_prompt = self.fill(self.keyinfo_template, chunk_text)

        summary = self.llm.chat(summary_prompt)
        key_info_raw = self.llm.chat(key_prompt)

        try:
            key_info = json.loads(key_info_raw)
        except:
            key_info = {"error": "INVALID_JSON", "raw": key_info_raw}

        return ChunkResult(
            chunk_id=chunk_id,
            text=chunk_text,
            summary=summary,
            key_info=key_info
        )

