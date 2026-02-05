from typing import List
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

class GenerateRequest(BaseSchema):
    tenant_id: str
    user_id: str
    prompt: str
    top_k: int = 4

class Source(BaseSchema):
    id: str
    title: str
    snippet: str
    score: float

class EvidenceCheck(BaseSchema):
    consistency_score: float
    min_source_score: float
    flags: list[str]

class GenerateResponse(BaseSchema):
    answer: str
    sources: List[Source]
    confidence: float
    model_id: str
    evidence: EvidenceCheck

class IngestRequest(BaseSchema):
    id: str
    title: str
    text: str
