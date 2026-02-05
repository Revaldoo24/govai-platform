from typing import Any, Dict, List


def build_explanation(
    prompt: str,
    answer: str,
    sources: List[Dict[str, Any]],
    confidence: float,
    bias: Dict[str, Any],
    governance: Dict[str, Any],
    model_id: str,
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    avg_source_score = 0.0
    if sources:
        avg_source_score = round(sum(s["score"] for s in sources) / len(sources), 4)

    uncertainty = "low"
    if confidence < 0.2:
        uncertainty = "high"
    elif confidence < 0.4:
        uncertainty = "medium"

    if bias.get("risk_level") == "high":
        uncertainty = "high"

    return {
        "model": {
            "model_id": model_id,
            "confidence": confidence,
        },
        "sources": {
            "count": len(sources),
            "avg_score": avg_source_score,
            "items": sources,
        },
        "decisioning": {
            "status": governance.get("status"),
            "reasons": governance.get("reasons", []),
            "policy_hits": governance.get("policy_hits", []),
        },
        "evidence": evidence,
        "risk": {
            "bias_score": bias.get("bias_score"),
            "bias_risk": bias.get("risk_level"),
            "bias_metrics": bias.get("metrics", {}),
            "uncertainty": uncertainty,
        },
        "trace": {
            "prompt": prompt,
            "answer": answer,
        },
    }
