from typing import Dict, List, Tuple
from ..schemas import EvidenceItem, StakeholderSource


def compute_truth_score(stakeholders: List[StakeholderSource], evidence: List[EvidenceItem]) -> Tuple[Dict[str, int], Dict[str, float]]:
    if not stakeholders:
        return {"authority": 0, "consistency": 0, "freshness": 0, "evidence_strength": 0}, {"score": 0.0}

    authority = round(sum(source.authority for source in stakeholders) / len(stakeholders))
    evidence_strength = round(sum(item.relevance for item in evidence) / len(evidence)) if evidence else 0
    consistency = round(len([item for item in evidence if "No relevant" not in item.text]) / len(evidence) * 100) if evidence else 0
    freshness = 100

    score = authority * 0.4 + evidence_strength * 0.3 + consistency * 0.2 + freshness * 0.1
    return {
        "authority": authority,
        "consistency": consistency,
        "freshness": freshness,
        "evidence_strength": evidence_strength,
    }, {"score": score}


def classify_truth(score: int) -> str:
    if score >= 90:
        return "TRUE"
    if score >= 70:
        return "LIKELY TRUE"
    if score >= 40:
        return "UNVERIFIED"
    if score >= 20:
        return "LIKELY FALSE"
    return "FALSE"


def build_explanation(score: int, validation: Dict[str, int], evidence: List[EvidenceItem]) -> Tuple[str, str]:
    classification = classify_truth(score)
    evidence_points = []
    for item in evidence:
        if "No relevant" not in item.text:
            evidence_points.append(f"Official evidence from {item.source}")
        else:
            evidence_points.append(f"No official evidence found for {item.source}")

    explanation = (
        f"Claim verified status: {classification}. "
        f"Score breakdown: authority={validation['authority']}%, evidence_strength={validation['evidence_strength']}%, "
        f"consistency={validation['consistency']}%, freshness={validation['freshness']}%. "
        f"Evidence: {'; '.join(evidence_points)}"
    )
    return classification, explanation
