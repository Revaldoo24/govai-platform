from typing import Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

class Source(BaseSchema):
    id: str
    title: str
    snippet: str
    score: float

class EvaluateRequest(BaseSchema):
    tenant_id: str
    user_id: str
    prompt: str
    answer: str
    sources: List[Source]
    confidence: float
    bias_score: float
    model_id: str
    consistency_score: float = 0.0
    evidence_flags: List[str] = []
    policy_mode: str = Field(default="enforce", description="enforce|advisory")

class PolicyCreate(BaseSchema):
    tenant_id: str
    name: str
    rule_type: str
    params: Dict[str, Any]
    enabled: bool = True

class PolicyResponse(BaseSchema):
    id: str
    tenant_id: str
    name: str
    rule_type: str
    params: Dict[str, Any]
    enabled: bool

class DecisionResponse(BaseSchema):
    decision_id: str
    status: str
    reasons: List[str]
    policy_hits: List[Dict[str, Any]]

class DecisionUpdate(BaseSchema):
    status: str
    reviewer: str
    notes: str = ""
