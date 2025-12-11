# Provide a small schema for ChunkResult. Use pydantic when available, else fallback to a dataclass.
try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except Exception:
    BaseModel = object
    PYDANTIC_AVAILABLE = False

from typing import Dict, Any

if PYDANTIC_AVAILABLE:
    from typing import List

    class ChunkResult(BaseModel):
        chunk_id: int
        text: str
        summary: str
        key_info: Dict[str, Any]
        topics: List[str] = []  # type: ignore

        # `model_dump` in pydantic v1 doesn't exist; ensure compatibility by providing a wrapper
        def model_dump(self):
            try:
                return super().model_dump()
            except Exception:
                try:
                    return self.dict()
                except Exception:
                    return {}

    class BackendSpec(BaseModel):
        provider: str
        model: str
        
else:
    from dataclasses import dataclass, asdict
    from typing import List

    @dataclass
    class ChunkResult:
        chunk_id: int
        text: str
        summary: str
        key_info: Dict[str, Any]
        topics: List[str] = []

        def dict(self):
            d = asdict(self)
            if d.get("topics") is None:
                d["topics"] = []
            return d

        def model_dump(self):
            return self.dict()
