from datetime import datetime
import time
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal
from .models import PolicyRule, Decision, AuditLog
from .schemas import EvaluateRequest, PolicyCreate, PolicyResponse, DecisionResponse, DecisionUpdate
from .policies import default_policies, evaluate_policies
from .audit import create_audit_log, create_decision

app = FastAPI(title="GovAI Governance", version="0.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def init_db():
    # Wait briefly for Postgres to be ready in containerized setups.
    last_error = None
    for _ in range(15):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as exc:
            last_error = exc
            time.sleep(2)
    raise last_error


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/policies", response_model=PolicyResponse)
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    rule = PolicyRule(
        tenant_id=payload.tenant_id,
        name=payload.name,
        rule_type=payload.rule_type,
        params=payload.params,
        enabled=payload.enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {
        "id": rule.id,
        "tenant_id": rule.tenant_id,
        "name": rule.name,
        "rule_type": rule.rule_type,
        "params": rule.params,
        "enabled": rule.enabled,
    }


@app.get("/policies", response_model=List[PolicyResponse])
def list_policies(tenant_id: str, db: Session = Depends(get_db)):
    rules = db.query(PolicyRule).filter(PolicyRule.tenant_id == tenant_id).all()
    return [
        {
            "id": rule.id,
            "tenant_id": rule.tenant_id,
            "name": rule.name,
            "rule_type": rule.rule_type,
            "params": rule.params,
            "enabled": rule.enabled,
        }
        for rule in rules
    ]


@app.post("/evaluate", response_model=DecisionResponse)
def evaluate(payload: EvaluateRequest, db: Session = Depends(get_db)):
    rules = db.query(PolicyRule).filter(PolicyRule.tenant_id == payload.tenant_id).all()
    if rules:
        policy_data = [
            {
                "id": rule.id,
                "tenant_id": rule.tenant_id,
                "name": rule.name,
                "rule_type": rule.rule_type,
                "params": rule.params,
                "enabled": rule.enabled,
            }
            for rule in rules
        ]
    else:
        policy_data = default_policies(payload.tenant_id)

    status, reasons, hits = evaluate_policies(
        policy_data,
        payload.prompt,
        payload.answer,
        payload.confidence,
        payload.bias_score,
        len(payload.sources),
        payload.consistency_score,
        payload.evidence_flags,
    )

    if payload.policy_mode == "advisory" and status == "rejected":
        status = "pending"
        reasons.append("Advisory mode: rejection downgraded to pending")

    audit = create_audit_log(
        db=db,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
        prompt=payload.prompt,
        answer=payload.answer,
        confidence=payload.confidence,
        bias_score=payload.bias_score,
        model_id=payload.model_id,
        decision_status=status,
    )

    decision = create_decision(
        db=db,
        audit_id=audit.id,
        tenant_id=payload.tenant_id,
        status=status,
        reasons=reasons,
        policy_hits=hits,
    )

    return {
        "decision_id": decision.id,
        "status": decision.status,
        "reasons": decision.reasons,
        "policy_hits": decision.policy_hits,
    }


@app.post("/decisions/{decision_id}")
def update_decision(decision_id: str, payload: DecisionUpdate, db: Session = Depends(get_db)):
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision.status = payload.status
    decision.reviewer = payload.reviewer
    decision.review_notes = payload.notes
    decision.updated_at = datetime.utcnow()
    db.commit()

    return {"status": "updated", "decision_id": decision_id}


@app.get("/decisions")
def list_decisions(tenant_id: str, status: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    query = db.query(Decision).filter(Decision.tenant_id == tenant_id)
    if status:
        query = query.filter(Decision.status == status)
    decisions = query.order_by(Decision.created_at.desc()).limit(limit).all()
    return [
        {
            "id": d.id,
            "status": d.status,
            "reasons": d.reasons,
            "policy_hits": d.policy_hits,
            "created_at": d.created_at.isoformat(),
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
        for d in decisions
    ]


@app.get("/decisions/{decision_id}/detail")
def decision_detail(decision_id: str, db: Session = Depends(get_db)):
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    audit = db.query(AuditLog).filter(AuditLog.id == decision.audit_id).first()
    return {
        "decision": {
            "id": decision.id,
            "status": decision.status,
            "reasons": decision.reasons,
            "policy_hits": decision.policy_hits,
            "reviewer": decision.reviewer,
            "review_notes": decision.review_notes,
            "created_at": decision.created_at.isoformat(),
            "updated_at": decision.updated_at.isoformat() if decision.updated_at else None,
        },
        "audit": {
            "tenant_id": audit.tenant_id if audit else None,
            "user_id": audit.user_id if audit else None,
            "prompt": audit.prompt if audit else None,
            "answer": audit.answer if audit else None,
            "confidence": audit.confidence if audit else None,
            "bias_score": audit.bias_score if audit else None,
            "model_id": audit.model_id if audit else None,
            "decision_status": audit.decision_status if audit else None,
            "created_at": audit.created_at.isoformat() if audit else None,
        },
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(
        """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>GovAI Governance Dashboard</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; background: #f7f7f9; }
      h1 { margin-bottom: 8px; }
      .row { display: flex; gap: 16px; flex-wrap: wrap; }
      .card { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 16px; flex: 1 1 320px; }
      label { display: block; margin: 8px 0 4px; }
      input, textarea, select { width: 100%; padding: 8px; }
      button { margin-top: 8px; padding: 8px 12px; }
      pre { white-space: pre-wrap; background: #fafafa; padding: 8px; border-radius: 6px; }
      .small { font-size: 12px; color: #555; }
    </style>
  </head>
  <body>
    <h1>GovAI Governance Dashboard</h1>
    <div class="small">Use this page to review pending decisions and approve or reject them.</div>

    <div class="row">
      <div class="card">
        <h3>Load Decisions</h3>
        <label>Tenant ID</label>
        <input id="tenantId" value="gov-dept-a"/>
        <label>Status</label>
        <select id="status">
          <option value="">All</option>
          <option value="pending" selected>Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <button onclick="loadDecisions()">Load</button>
        <pre id="decisionList"></pre>
      </div>

      <div class="card">
        <h3>Decision Detail</h3>
        <label>Decision ID</label>
        <input id="decisionId"/>
        <button onclick="loadDetail()">Load Detail</button>
        <pre id="decisionDetail"></pre>
      </div>

      <div class="card">
        <h3>Review Decision</h3>
        <label>Decision ID</label>
        <input id="reviewDecisionId"/>
        <label>Status</label>
        <select id="reviewStatus">
          <option value="approved">Approve</option>
          <option value="rejected">Reject</option>
          <option value="pending">Keep Pending</option>
        </select>
        <label>Reviewer</label>
        <input id="reviewer" placeholder="reviewer-name"/>
        <label>Notes</label>
        <textarea id="reviewNotes" rows="3"></textarea>
        <button onclick="submitReview()">Submit</button>
        <pre id="reviewResult"></pre>
      </div>
    </div>

    <script>
      async function loadDecisions() {
        const tenantId = document.getElementById('tenantId').value;
        const status = document.getElementById('status').value;
        const qs = new URLSearchParams({ tenant_id: tenantId });
        if (status) qs.set('status', status);
        const resp = await fetch('/decisions?' + qs.toString());
        const data = await resp.json();
        document.getElementById('decisionList').textContent = JSON.stringify(data, null, 2);
      }
      async function loadDetail() {
        const decisionId = document.getElementById('decisionId').value;
        const resp = await fetch('/decisions/' + decisionId + '/detail');
        const data = await resp.json();
        document.getElementById('decisionDetail').textContent = JSON.stringify(data, null, 2);
      }
      async function submitReview() {
        const decisionId = document.getElementById('reviewDecisionId').value;
        const status = document.getElementById('reviewStatus').value;
        const reviewer = document.getElementById('reviewer').value;
        const notes = document.getElementById('reviewNotes').value;
        const resp = await fetch('/decisions/' + decisionId, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status, reviewer, notes })
        });
        const data = await resp.json();
        document.getElementById('reviewResult').textContent = JSON.stringify(data, null, 2);
      }
    </script>
  </body>
</html>
        """
    )


@app.get("/bias/drift")
def bias_drift(tenant_id: str, window: int = 50, threshold: float = 0.1, db: Session = Depends(get_db)):
    window = max(10, min(window, 500))
    scores = (
        db.query(AuditLog.bias_score)
        .filter(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(window * 2)
        .all()
    )
    flat = [row[0] for row in scores]
    if len(flat) < window * 2:
        return {
            "tenant_id": tenant_id,
            "status": "insufficient_data",
            "required": window * 2,
            "available": len(flat),
        }

    recent = flat[:window]
    prev = flat[window : window * 2]
    recent_mean = sum(recent) / len(recent)
    prev_mean = sum(prev) / len(prev)
    drift_score = abs(recent_mean - prev_mean)

    return {
        "tenant_id": tenant_id,
        "window": window,
        "recent_mean": round(recent_mean, 4),
        "previous_mean": round(prev_mean, 4),
        "drift_score": round(drift_score, 4),
        "status": "drift_detected" if drift_score >= threshold else "stable",
        "threshold": threshold,
    }
