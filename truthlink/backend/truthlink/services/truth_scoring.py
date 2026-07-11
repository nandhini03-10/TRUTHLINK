from typing import Dict, List, Tuple
from truthlink.schemas import EvidenceItem, StakeholderSource

POSITIVE_FILM_TERMS = {
    "hit", "blockbuster", "success", "superhit", "smash", "record", "record-breaking",
    "box office success", "box office hit", "went on to gross", "grossed", "earned", "revenue", "collection"
}
NEGATIVE_FILM_TERMS = {
    "flop", "bomb", "failure", "disaster", "underperform", "poor", "average", "struggle",
    "struggled", "loss", "low collection", "tank", "tanked", "box office failure", "box office flop",
    "failed to", "failed", "deficit"
}


def _claim_polarity(claim: str) -> int:
    lower = claim.lower()
    if any(term in lower for term in NEGATIVE_FILM_TERMS):
        return -1
    if any(term in lower for term in POSITIVE_FILM_TERMS):
        return 1
    return 0


def compute_truth_score(
    stakeholders: List[StakeholderSource],
    evidence: List[EvidenceItem],
    claim_type: str = "general",
    claim_text: str = ""
) -> Tuple[Dict[str, int], Dict[str, float]]:
    if not stakeholders:
        return {"authority": 0, "consistency": 0, "freshness": 0, "evidence_strength": 0}, {"score": 0.0}

    # Check if we have any high-authority sources
    has_high_authority = any(source.authority >= 85 for source in stakeholders)
    
    # For sensitive claims (celebrity, political), require high-authority sources
    if claim_type in ["celebrity", "political"] and not has_high_authority:
        # Penalize low-authority sources heavily for sensitive claims
        authority = min(round(sum(source.authority for source in stakeholders) / len(stakeholders)), 40)
    else:
        authority = round(sum(source.authority for source in stakeholders) / len(stakeholders))
    
    claim_polarity = _claim_polarity(claim_text)
    evidence_strength = round(sum(item.relevance for item in evidence) / len(evidence)) if evidence else 0
    contradiction_penalty = round(sum(1 for item in evidence if item.polarity != 0 and claim_polarity != 0 and item.polarity != claim_polarity) / len(evidence) * 100) if evidence else 0
    consistency = round(sum(1 for item in evidence if item.relevance >= 50 and (item.polarity == 0 or item.polarity == claim_polarity)) / len(evidence) * 100) if evidence else 0
    weighted_authority = round(sum(source.authority * (item.relevance / 100) for source, item in zip(stakeholders, evidence)) / len(stakeholders)) if evidence else authority
    freshness = 100

    score = weighted_authority * 0.40 + evidence_strength * 0.30 + consistency * 0.20 + (100 - contradiction_penalty) * 0.05 + freshness * 0.05
    return {
        "authority": weighted_authority,
        "consistency": consistency,
        "freshness": freshness,
        "evidence_strength": evidence_strength,
    }, {"score": score}



def classify_truth(score: int) -> str:
    if score >= 85:
        return "TRUE"
    if score >= 65:
        return "LIKELY TRUE"
    if score >= 45:
        return "UNVERIFIED"
    if score >= 25:
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
