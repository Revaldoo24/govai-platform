from typing import Any, Dict, List
from pydantic import BaseModel

class Source(BaseModel):
    id: str
    title: str
    snippet: str
    score: float

class ExplainRequest(BaseModel):
    tenant_id: str
    user_id: str
    prompt: str
    answer: str
    sources: List[Source]
    confidence: float
    bias: Dict[str, Any]
    governance: Dict[str, Any]
    model_id: str
    evidence: Dict[str, Any]

class ExplainResponse(BaseModel):
    explanation: Dict[str, Any]
