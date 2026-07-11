from fastapi import APIRouter
from ..schemas import VerifyRequest, VerifyResponse, StakeholderSource, EvidenceItem
from ..services.claim_analyzer import analyze_claim
from ..services.entity_extractor import extract_entities
from ..services.stakeholder_finder import load_stakeholders, find_stakeholders
from ..services.evidence_collector import collect_evidence
from ..services.truth_scoring import build_explanation, compute_truth_score

router = APIRouter()

stakeholder_store = load_stakeholders()

@router.post("/verify", response_model=VerifyResponse)
def verify_claim(request: VerifyRequest):
    claim_data = analyze_claim(request.claim)
    entities = extract_entities(claim_data["claim"])
    stakeholders = find_stakeholders(claim_data["claim"], entities, stakeholder_store)
    evidence = collect_evidence(claim_data["claim"], entities, stakeholders)
    validation, score_components = compute_truth_score(stakeholders, evidence)
    truth_score = round(score_components["score"])
    classification, explanation = build_explanation(truth_score, validation, evidence)

    return {
        "claim": claim_data["claim"],
        "keywords": claim_data["keywords"],
        "entities": entities,
        "stakeholders": stakeholders,
        "evidence": evidence,
        "validation": validation,
        "truth_score": truth_score,
        "classification": classification,
        "explanation": explanation,
    }
