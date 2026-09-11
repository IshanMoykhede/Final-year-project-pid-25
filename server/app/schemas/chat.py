from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    document_id: str
    question: str
    use_1hop_expansion: bool = True

class RetrievedClause(BaseModel):
    chunk_id: str
    chunk_no: int
    text: str
    aliases: List[str] = []
    similarity: Optional[float] = None
    is_expanded: bool = False

class ChatResponse(BaseModel):
    success: bool
    answer: str
    primary_clauses: List[RetrievedClause]
    expanded_clauses: List[RetrievedClause]
