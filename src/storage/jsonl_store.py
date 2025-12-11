import json
from pathlib import Path
from typing import Iterable
from ai.schema import ChunkResult

# JSONL persistence supports both pydantic and dataclass backed ChunkResult


class JSONLStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _to_dict(self, r):
        # Accept dict, pydantic BaseModel, dataclass, or objects with dict-like access
        if isinstance(r, dict):
            return r
        if hasattr(r, "model_dump"):
            try:
                return r.model_dump()
            except Exception:
                pass
        if hasattr(r, "dict"):
            try:
                return r.dict()
            except Exception:
                pass
        if hasattr(r, "__dict__"):
            return vars(r)
        # fallback: try to coerce by reading attributes
        try:
            return {k: getattr(r, k) for k in ["chunk_id", "text", "summary", "key_info", "topics"] if hasattr(r, k)}
        except Exception:
            raise TypeError("Unsupported result type for JSONL serialization")

    def save_chunk(self, result: ChunkResult):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(self._to_dict(result), ensure_ascii=False) + "\n")

    def save_many(self, results: Iterable[ChunkResult]):
        with self.path.open("a", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(self._to_dict(r), ensure_ascii=False) + "\n")

    def load_all(self) -> list[ChunkResult]:
        results = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                results.append(ChunkResult(**data))
        return results
