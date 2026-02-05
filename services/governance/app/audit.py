from typing import Any, Dict, List
from sqlalchemy.orm import Session
from .models import AuditLog, Decision


def create_audit_log(
    db: Session,
    tenant_id: str,
    user_id: str,
    prompt: str,
    answer: str,
    confidence: float,
    bias_score: float,
    model_id: str,
    decision_status: str,
) -> AuditLog:
    audit = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        prompt=prompt,
        answer=answer,
        confidence=confidence,
        bias_score=bias_score,
        model_id=model_id,
        decision_status=decision_status,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def create_decision(
    db: Session,
    audit_id: str,
    tenant_id: str,
    status: str,
    reasons: List[str],
    policy_hits: List[Dict[str, Any]],
) -> Decision:
    decision = Decision(
        audit_id=audit_id,
        tenant_id=tenant_id,
        status=status,
        reasons=reasons,
        policy_hits=policy_hits,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision
