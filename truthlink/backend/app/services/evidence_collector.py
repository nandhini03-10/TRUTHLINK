import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from ..schemas import EvidenceItem, StakeholderSource


def fetch_url_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
        if paragraphs:
            return "\n".join(paragraphs[:8]).strip()
        return soup.get_text(separator=" ", strip=True)[:1000]
    except Exception as exc:
        return f"Failed to fetch source ({url}): {exc}"


def collect_evidence(claim: str, entities: Dict[str, List[str]], stakeholders: List[StakeholderSource]) -> List[EvidenceItem]:
    evidence_records = []
    for stakeholder in stakeholders:
        text = fetch_url_text(stakeholder.url)
        matched = any(entity.lower() in text.lower() for entity_list in entities.values() for entity in entity_list)
        relevance = 90 if matched else 40
        evidence_records.append(
            EvidenceItem(
                source=stakeholder.name,
                kind=stakeholder.type,
                text=text,
                date="2026-06-25",
                authenticity=stakeholder.authority,
                relevance=relevance,
            )
        )
    return evidence_records
