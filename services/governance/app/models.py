import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)
    params = Column(JSON, nullable=False, default=dict)
    enabled = Column(Boolean, nullable=False, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    prompt = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    bias_score = Column(Float, nullable=False)
    model_id = Column(String, nullable=False)
    decision_status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    decision = relationship("Decision", back_populates="audit", uselist=False)

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    audit_id = Column(String, ForeignKey("audit_logs.id"), nullable=False)
    tenant_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    reasons = Column(JSON, nullable=False, default=list)
    policy_hits = Column(JSON, nullable=False, default=list)
    reviewer = Column(String, nullable=True)
    review_notes = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    audit = relationship("AuditLog", back_populates="decision")
