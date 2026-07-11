import re
from typing import Dict, List
from ..schemas import StakeholderSource
from truthlink.services.source_discovery import discover_sources_for_query


def normalize_query(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", text)
    return " ".join(part for part in cleaned.split() if part)


def load_stakeholders() -> Dict[str, List[StakeholderSource]]:
    return {}


def find_stakeholders(claim: str, entities: Dict[str, List[str]], store: Dict[str, List[StakeholderSource]]) -> List[StakeholderSource]:
    query_parts = []
    for entity_type in ["company", "person", "location"]:
        query_parts.extend(entities.get(entity_type, []))

    if claim:
        query_parts.append(claim)

    query = normalize_query(" ".join(query_parts)).strip()
    if not query:
        return []

    discovered = discover_sources_for_query(query)
    sources = []
    for url, title, kind, authority in discovered:
        sources.append(
            StakeholderSource(
                name=title or url,
                type=kind,
                url=url,
                authority=authority,
            )
        )
    return sources
