import argparse
import json
from app.services.claim_analyzer import analyze_claim
from app.services.entity_extractor import extract_entities
from app.services.stakeholder_finder import load_stakeholders, find_stakeholders
from app.services.evidence_collector import collect_evidence
from app.services.truth_scoring import build_explanation, compute_truth_score


def verify_claim(claim: str) -> dict:
    claim_data = analyze_claim(claim)
    entities = extract_entities(claim_data["claim"])
    stakeholders = find_stakeholders(entities, load_stakeholders())
    evidence = collect_evidence(claim_data["claim"], entities, stakeholders)
    validation, score_components = compute_truth_score(stakeholders, evidence)
    truth_score = round(score_components["score"])
    classification, explanation = build_explanation(truth_score, validation, evidence)

    return {
        "claim": claim_data["claim"],
        "keywords": claim_data["keywords"],
        "entities": entities,
        "stakeholders": [stakeholder.model_dump() for stakeholder in stakeholders],
        "evidence": [item.model_dump() for item in evidence],
        "validation": validation,
        "truth_score": truth_score,
        "classification": classification,
        "explanation": explanation,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TruthLink claim verification in pure Python.")
    parser.add_argument("claim", nargs="*", help="The claim to verify.")
    args = parser.parse_args()

    if args.claim:
        claim_text = " ".join(args.claim)
    else:
        claim_text = input("Enter the claim to verify: ").strip()

    if not claim_text:
        raise SystemExit("No claim provided.")

    result = verify_claim(claim_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
