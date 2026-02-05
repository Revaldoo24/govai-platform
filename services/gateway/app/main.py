from fastapi import FastAPI, Header, HTTPException, Depends
from .config import settings
from .schemas import GenerateRequest, GenerateResponse
from .clients import call_rag, call_bias, call_governance, call_explain

app = FastAPI(title="GovAI Gateway", version="0.1.0")


def enforce_security(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
):
    if settings.enforce_api_key:
        if not settings.api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        if x_api_key != settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="Missing X-Tenant-Id header")
    return x_tenant_id

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, tenant_header: str = Depends(enforce_security)):
    if tenant_header != req.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant header mismatch")
    rag_payload = {
        "tenant_id": req.tenant_id,
        "user_id": req.user_id,
        "prompt": req.prompt,
        "top_k": req.top_k,
    }
    rag = await call_rag(rag_payload)

    bias_payload = {
        "tenant_id": req.tenant_id,
        "user_id": req.user_id,
        "prompt": req.prompt,
        "answer": rag["answer"],
    }
    bias = await call_bias(bias_payload)

    gov_payload = {
        "tenant_id": req.tenant_id,
        "user_id": req.user_id,
        "prompt": req.prompt,
        "answer": rag["answer"],
        "sources": rag["sources"],
        "confidence": rag["confidence"],
        "bias_score": bias["bias_score"],
        "policy_mode": req.policy_mode,
        "model_id": rag.get("model_id", "unknown"),
        "consistency_score": rag.get("evidence", {}).get("consistency_score", 0.0),
        "evidence_flags": rag.get("evidence", {}).get("flags", []),
    }
    governance = await call_governance(gov_payload)

    explain_payload = {
        "tenant_id": req.tenant_id,
        "user_id": req.user_id,
        "prompt": req.prompt,
        "answer": rag["answer"],
        "sources": rag["sources"],
        "confidence": rag["confidence"],
        "bias": bias,
        "governance": governance,
        "model_id": rag.get("model_id", "unknown"),
        "evidence": rag.get("evidence", {}),
    }
    explainability = await call_explain(explain_payload)

    return {
        "answer": rag["answer"],
        "sources": rag["sources"],
        "confidence": rag["confidence"],
        "model_id": rag.get("model_id", "unknown"),
        "bias": bias,
        "governance": governance,
        "explainability": explainability,
        "evidence": rag.get("evidence", {}),
    }
