from fastapi import FastAPI
from .schemas import ExplainRequest, ExplainResponse
from .explain import build_explanation

app = FastAPI(title="GovAI Explainability", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest):
    explanation = build_explanation(
        prompt=req.prompt,
        answer=req.answer,
        sources=[s.model_dump() for s in req.sources],
        confidence=req.confidence,
        bias=req.bias,
        governance=req.governance,
        model_id=req.model_id,
        evidence=req.evidence,
    )
    return {"explanation": explanation}
