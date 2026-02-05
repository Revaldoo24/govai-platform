from fastapi import FastAPI
from .schemas import BiasRequest, BiasResponse
from .bias import score_bias, risk_label, bias_metrics

app = FastAPI(title="GovAI Bias", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze", response_model=BiasResponse)
def analyze(req: BiasRequest):
    combined = f"{req.prompt}\n{req.answer}"
    score, flagged = score_bias(combined)
    return {
        "bias_score": score,
        "risk_level": risk_label(score),
        "flagged_terms": flagged,
        "metrics": bias_metrics(flagged),
    }
