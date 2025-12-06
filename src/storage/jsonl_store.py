import json
from pathlib import Path
from typing import Iterable
from ai.schema import ChunkResult


class JSONLStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_chunk(self, result: ChunkResult):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.model_dump(), ensure_ascii=False) + "\n")

    def save_many(self, results: Iterable[ChunkResult]):
        with self.path.open("a", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r.model_dump(), ensure_ascii=False) + "\n")

    def load_all(self) -> list[ChunkResult]:
        results = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                results.append(ChunkResult(**data))
        return results
