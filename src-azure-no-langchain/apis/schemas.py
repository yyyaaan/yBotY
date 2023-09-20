from pydantic import BaseModel
from typing import List


class FileEmbeddingRequest(BaseModel):
    file_path: str = "./samples/cache.txt"
    max_tokens: int = 1000
    overlapping_sentences: int = 2
    category: str = "unset"
    tier: int = 0


class RouterChainEntry(BaseModel):
    question: str
    docIds: str = "71225838e3174e77b700d3c095a8195d"


class OutputTextChunkRequest(BaseModel):
    count: int
    tokens: List[int]
    chunks: List[str]
