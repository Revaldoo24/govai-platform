from typing import List
from pydantic import BaseModel

class BiasRequest(BaseModel):
    tenant_id: str
    user_id: str
    prompt: str
    answer: str

class BiasResponse(BaseModel):
    bias_score: float
    risk_level: str
    flagged_terms: List[str]
    metrics: dict
