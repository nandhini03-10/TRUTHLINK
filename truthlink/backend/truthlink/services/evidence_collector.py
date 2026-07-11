import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from truthlink.schemas import EvidenceItem, StakeholderSource
from truthlink.services.ai_engine import validate_source

STOPWORDS = {
    "is", "are", "was", "were", "be", "being", "been", "the", "a", "an", "in", "on", "at", "of",
    "for", "with", "by", "to", "from", "that", "this", "these", "those", "it", "its", "as",
    "got", "have", "has", "had", "do", "does", "did", "will", "would", "should", "could", "may", "might",
    "today", "morning", "evening", "night", "yesterday", "now"
}


def fetch_url_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
        text = "\n".join(paragraphs[:8]).strip() if paragraphs else soup.get_text(separator=" ", strip=True)[:1000]
        return text
    except Exception:
        return ""


NEGATIVE_TERMS = {
    "not", "no", "none", "false", "fake", "hoax", "denies", "denied", "debunk", "mistaken", "wrong", "untrue"
}

NEGATIVE_PHRASES = {
    "not arrested", "no arrest", "no evidence", "fake news", "hoax", "denied arrest",
    "not true", "untrue", "false report", "wrongly reported", "not real"
}

POSITIVE_FILM_TERMS = {
    "hit", "blockbuster", "success", "superhit", "smash", "record", "record-breaking", "rosy", "crowd-puller",
    "hit or flop", "box office success", "boxed office hit", "box office hit", "went on to gross", "grossed", "earned", "revenue", "collection"
}

NEGATIVE_FILM_TERMS = {
    "flop", "bomb", "failure", "disaster", "underperform", "poor", "average", "struggle", "struggled", "loss", "low collection",
    "tank", "tanked", "box office failure", "box office flop", "failed to", "failed", "deficit"
}


def _count_terms(text: str, terms: set[str]) -> int:
    return sum(1 for term in terms if term in text)


def _determine_polarity(text: str) -> int:
    text_lower = text.lower()
    positive = _count_terms(text_lower, POSITIVE_FILM_TERMS)
    negative = _count_terms(text_lower, NEGATIVE_FILM_TERMS)
    if positive > negative:
        return 1
    if negative > positive:
        return -1
    return 0


def _extract_keywords(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def _assess_relevance(claim: str, entities: Dict[str, List[str]], text: str, title: str = "") -> tuple[int, int]:
    combined_text = f"{title}\n{text}".lower()
    entity_match = any(entity.lower() in combined_text for entity_list in entities.values() for entity in entity_list)
    claim_keywords = _extract_keywords(claim)
    keyword_matches = [keyword for keyword in claim_keywords if keyword in combined_text]
    keyword_match_count = len(set(keyword_matches))

    action_terms = {
        "arrest", "arrested", "detained", "charged", "booked", "raided", "died", "dies", "death", "dead",
        "suicide", "killed", "injured", "attack", "hacked", "assaulted", "shot", "collision", "crash",
        "run", "runs", "running", "found", "founded", "launch", "launched", "startup", "movie", "film", "upcoming", "next"
    }
    has_action_term = any(term in claim.lower() for term in action_terms)
    action_in_text = any(term in combined_text for term in action_terms)
    negative_match = any(phrase in combined_text for phrase in NEGATIVE_PHRASES)
    if not negative_match:
        negative_match = any(term in combined_text and any(action in combined_text for action in action_terms) for term in NEGATIVE_TERMS)

    claim_polarity = _determine_polarity(claim)
    text_polarity = _determine_polarity(combined_text)
    polarity = text_polarity

    if entity_match and negative_match:
        return 0, polarity

    if entity_match and claim_polarity != 0:
        if text_polarity == claim_polarity:
            return 90, polarity
        if text_polarity == 0:
            if keyword_match_count >= max(2, len(claim_keywords) // 2) and action_in_text:
                return 50, polarity
            return 10, polarity
        return 0, polarity

    if entity_match:
        if polarity < 0:
            return 90, polarity
        if polarity > 0:
            return 10, polarity
        if has_action_term and action_in_text and keyword_match_count >= max(2, len(claim_keywords) // 2):
            return 70, polarity
        if has_action_term and action_in_text:
            return 50, polarity
        if keyword_match_count >= max(2, len(claim_keywords) // 2):
            return 60, polarity
        return 30, polarity

    if keyword_match_count >= 3:
        return 40, polarity
    return 0, polarity


def collect_evidence(claim: str, entities: Dict[str, List[str]], stakeholders: List[StakeholderSource]) -> List[EvidenceItem]:
    evidence_records = []
    for stakeholder in stakeholders:
        text = fetch_url_text(stakeholder.url)
        relevance, polarity = _assess_relevance(claim, entities, text, stakeholder.name)
        ai_score = validate_source(claim, stakeholder.name, text, entities)
        relevance = max(relevance, ai_score)
        evidence_records.append(
            EvidenceItem(
                source=stakeholder.name,
                kind=stakeholder.type,
                text=text,
                date="2026-06-25",
                authenticity=stakeholder.authority,
                relevance=relevance,
                polarity=polarity,
            )
        )
    return evidence_records
