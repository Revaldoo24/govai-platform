from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

class GenerateRequest(BaseSchema):
    tenant_id: str
    user_id: str
    prompt: str
    top_k: int = 4
    policy_mode: Optional[str] = Field(default="enforce", description="enforce|advisory")

class Source(BaseSchema):
    id: str
    title: str
    snippet: str
    score: float

class RagResponse(BaseSchema):
    answer: str
    sources: List[Source]
    confidence: float
    model_id: str
    evidence: Dict[str, Any]

class BiasResponse(BaseSchema):
    bias_score: float
    risk_level: str
    flagged_terms: List[str]
    metrics: Dict[str, Any]

class GovernanceDecision(BaseSchema):
    decision_id: str
    status: str
    reasons: List[str]
    policy_hits: List[Dict[str, Any]]

class ExplainabilityResponse(BaseSchema):
    explanation: Dict[str, Any]

class GenerateResponse(BaseSchema):
    answer: str
    sources: List[Source]
    confidence: float
    model_id: str
    bias: BiasResponse
    governance: GovernanceDecision
    explainability: ExplainabilityResponse
    evidence: Dict[str, Any]
