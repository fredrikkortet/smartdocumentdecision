from pydantic import BaseModel
from typing import List, Dict, Any


class ChunkResult(BaseModel):
    chunk_id: int
    text: str
    summary: str
    key_info: Dict[str, Any]

