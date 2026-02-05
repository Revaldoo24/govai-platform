from typing import List, Tuple

SENSITIVE_TERMS = [
    "race", "ethnicity", "religion", "gender", "disability", "nationality",
    "age", "immigrant", "minority", "majority", "poverty",
]

RISK_LEVELS = [
    (0.0, "low"),
    (0.2, "medium"),
    (0.5, "high"),
]


def score_bias(text: str) -> Tuple[float, List[str]]:
    lowered = text.lower()
    flagged = [term for term in SENSITIVE_TERMS if term in lowered]
    if not flagged:
        return 0.0, []

    score = min(1.0, len(flagged) / max(1, len(SENSITIVE_TERMS) // 2))
    return round(score, 4), flagged


def risk_label(score: float) -> str:
    label = "low"
    for threshold, name in RISK_LEVELS:
        if score >= threshold:
            label = name
    return label


def bias_metrics(flagged: List[str]) -> dict:
    flagged_count = len(flagged)
    sensitive_count = len(SENSITIVE_TERMS)
    rate = round(flagged_count / sensitive_count, 4) if sensitive_count else 0.0
    return {
        "flagged_count": flagged_count,
        "sensitive_terms_total": sensitive_count,
        "sensitive_term_rate": rate,
    }
