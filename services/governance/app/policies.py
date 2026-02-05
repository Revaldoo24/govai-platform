from typing import Any, Dict, List, Tuple
from .config import settings


def default_policies(tenant_id: str) -> List[Dict[str, Any]]:
    policies = [
        {
            "id": "default-confidence",
            "tenant_id": tenant_id,
            "name": "Minimum Confidence",
            "rule_type": "REQUIRE_CONFIDENCE",
            "params": {"min_confidence": settings.default_confidence},
            "enabled": True,
        }
    ]
    policies.append(
        {
            "id": "default-grounding",
            "tenant_id": tenant_id,
            "name": "Minimum Grounding Consistency",
            "rule_type": "REQUIRE_GROUNDING",
            "params": {"min_consistency": 0.2},
            "enabled": True,
        }
    )
    if settings.require_citations:
        policies.append(
            {
                "id": "default-citations",
                "tenant_id": tenant_id,
                "name": "Require Citations",
                "rule_type": "REQUIRE_CITATIONS",
                "params": {"min_sources": 1},
                "enabled": True,
            }
        )
    return policies


def evaluate_policies(
    policies: List[Dict[str, Any]],
    prompt: str,
    answer: str,
    confidence: float,
    bias_score: float,
    sources_count: int,
    consistency_score: float,
    evidence_flags: List[str],
) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    status = "approved"
    reasons: List[str] = []
    hits: List[Dict[str, Any]] = []

    for policy in policies:
        if not policy.get("enabled", True):
            continue

        rule_type = policy["rule_type"]
        params = policy.get("params", {})

        if rule_type == "REQUIRE_CONFIDENCE":
            min_conf = float(params.get("min_confidence", 0.0))
            if confidence < min_conf:
                if status != "rejected":
                    status = "pending"
                reasons.append(f"Confidence below threshold {min_conf}")
                hits.append({"policy_id": policy["id"], "rule": rule_type})

        if rule_type == "REQUIRE_CITATIONS":
            min_sources = int(params.get("min_sources", 1))
            if sources_count < min_sources:
                if status != "rejected":
                    status = "pending"
                reasons.append("Insufficient citations")
                hits.append({"policy_id": policy["id"], "rule": rule_type})

        if rule_type == "REQUIRE_GROUNDING":
            min_consistency = float(params.get("min_consistency", 0.0))
            if consistency_score < min_consistency:
                if status != "rejected":
                    status = "pending"
                reasons.append(f"Grounding consistency below {min_consistency}")
                hits.append({"policy_id": policy["id"], "rule": rule_type})
            if evidence_flags:
                if status != "rejected":
                    status = "pending"
                reasons.append("Evidence alignment flags detected")
                hits.append({"policy_id": policy["id"], "rule": rule_type})

        if rule_type == "BLOCKLIST_TERM":
            terms = [t.lower() for t in params.get("terms", [])]
            lowered = f"{prompt}\n{answer}".lower()
            if any(term in lowered for term in terms):
                status = "rejected"
                reasons.append("Blocked term detected")
                hits.append({"policy_id": policy["id"], "rule": rule_type})

        if rule_type == "MAX_BIAS":
            max_bias = float(params.get("max_bias", 1.0))
            if bias_score > max_bias:
                if status != "rejected":
                    status = "pending"
                reasons.append("Bias score above limit")
                hits.append({"policy_id": policy["id"], "rule": rule_type})

        if rule_type == "REQUIRE_HUMAN_REVIEW":
            if params.get("always", False):
                if status != "rejected":
                    status = "pending"
                reasons.append("Manual review required")
                hits.append({"policy_id": policy["id"], "rule": rule_type})
            else:
                if bias_score > float(params.get("if_bias_over", 1.1)):
                    if status != "rejected":
                        status = "pending"
                    reasons.append("Manual review due to bias")
                    hits.append({"policy_id": policy["id"], "rule": rule_type})
                if confidence < float(params.get("if_confidence_below", -1.0)):
                    if status != "rejected":
                        status = "pending"
                    reasons.append("Manual review due to low confidence")
                    hits.append({"policy_id": policy["id"], "rule": rule_type})

    return status, reasons, hits
