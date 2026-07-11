from typing import Any, Dict, List
import json


def _format_items(items: List[str]) -> str:
    if not items:
        return "  - None"
    return "\n".join(f"  - {item}" for item in items)


def _format_keyed_list(items: Dict[str, List[str]]) -> str:
    if not items:
        return "  - None"
    lines = []
    for key, values in items.items():
        values_text = ", ".join(values) if values else "None"
        lines.append(f"  {key}: {values_text}")
    return "\n".join(lines)


def _format_stakeholders(stakeholders: List[Dict[str, Any]]) -> str:
    if not stakeholders:
        return "  - None"
    lines = []
    for item in stakeholders:
        lines.append(
            f"  - {item['name']} ({item['type']})\n"
            f"      URL: {item['url']}\n"
            f"      Authority: {item['authority']}"
        )
    return "\n".join(lines)


def _format_evidence(evidence: List[Dict[str, Any]]) -> str:
    if not evidence:
        return "  - None"
    lines = []
    for item in evidence:
        lines.append(
            f"  - Source: {item['source']} ({item['kind']})\n"
            f"      Date: {item['date']}\n"
            f"      Authenticity: {item['authenticity']}\n"
            f"      Relevance: {item['relevance']}\n"
            f"      Text: {item['text']}"
        )
    return "\n".join(lines)


def _format_top_sources(evidence: List[Dict[str, Any]], max_items: int = 3) -> str:
    if not evidence:
        return "  - None"

    lines = []
    for idx, item in enumerate(evidence[:max_items], start=1):
        snippet = item["text"].replace("\n", " ").strip()
        if len(snippet) > 120:
            snippet = snippet[:117].rstrip() + "..."
        lines.append(
            f"  {idx}. {item['source']} ({item['kind']}, authority={item['authenticity']}%, relevance={item['relevance']}%)\n"
            f"      Snippet: {snippet}"
        )
    return "\n".join(lines)


def print_structured_result(result: Dict[str, Any], raw: bool = False, compact: bool = True) -> None:
    if raw:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if compact:
        # Summary-only format
        print("=== TruthLink Verification ===")
        print(f"Claim:          {result['claim']}")
        print(f"Classification: {result['classification']}")
        print()
        print("Metrics:")
        print(f"  Score:         {result['truth_score']}%")
        print(f"  Authority:     {result['validation']['authority']}%")
        print(f"  Evidence:      {result['validation']['evidence_strength']}%")
        print(f"  Consistency:   {result['validation']['consistency']}%")
        print(f"  Freshness:     {result['validation']['freshness']}%")
        print()
        print("Top Sources Checked:")
        print(_format_top_sources(result['evidence']))
        return

    # Verbose format (existing)
    print("=== TruthLink Verification Result ===")
    print(f"Claim: {result['claim']}")
    print(f"Truth Score: {result['truth_score']}%")
    print(f"Classification: {result['classification']}")
    print(f"Explanation: {result['explanation']}")
    print()
    print("Entities:")
    print(_format_keyed_list(result['entities']))
    print()
    print("Stakeholders:")
    print(_format_stakeholders(result['stakeholders']))
    print()
    print("Evidence:")
    print(_format_evidence(result['evidence']))
    print()
    print("Validation Metrics:")
    print(f"  - Authority: {result['validation']['authority']}%")
    print(f"  - Evidence Strength: {result['validation']['evidence_strength']}%")
    print(f"  - Consistency: {result['validation']['consistency']}%")
    print(f"  - Freshness: {result['validation']['freshness']}%")
