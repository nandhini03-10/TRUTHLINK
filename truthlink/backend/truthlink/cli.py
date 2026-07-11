import argparse
from truthlink.services.claim_analyzer import analyze_claim
from truthlink.services.entity_extractor import extract_entities
from truthlink.services.stakeholder_finder import load_stakeholders, find_stakeholders
from truthlink.services.evidence_collector import collect_evidence
from truthlink.services.truth_scoring import build_explanation, compute_truth_score
from truthlink.services.source_discovery import detect_claim_type
from truthlink.ui import print_structured_result


def verify_claim(claim: str) -> dict:
    claim_data = analyze_claim(claim)
    entities = extract_entities(claim_data["claim"])
    claim_type = detect_claim_type(claim_data["claim"])
    stakeholders = find_stakeholders(claim_data["claim"], entities, load_stakeholders())
    evidence = collect_evidence(claim_data["claim"], entities, stakeholders)
    validation, score_components = compute_truth_score(stakeholders, evidence, claim_type, claim_data["claim"])
    truth_score = round(score_components["score"])
    classification, explanation = build_explanation(truth_score, validation, evidence)

    return {
        "claim": claim_data["claim"],
        "keywords": claim_data["keywords"],
        "entities": entities,
        "claim_type": claim_type,
        "stakeholders": [stakeholder.model_dump() for stakeholder in stakeholders],
        "evidence": [item.model_dump() for item in evidence],
        "validation": validation,
        "truth_score": truth_score,
        "classification": classification,
        "explanation": explanation,
    }


def main():
    parser = argparse.ArgumentParser(description="Run TruthLink claim verification.")
    parser.add_argument("claim", nargs="+", help="The claim to verify.")
    parser.add_argument("--raw", action="store_true", help="Print raw JSON instead of formatted output.")
    parser.add_argument("--verbose", action="store_true", help="Print full detailed output.")
    args = parser.parse_args()

    claim_text = " ".join(args.claim)

    if not claim_text:
        parser.error("No claim provided.")

    result = verify_claim(claim_text)
    print_structured_result(result, raw=args.raw, compact=not args.verbose)


if __name__ == "__main__":
    main()
