import re
from typing import List, Dict

stopwords = {
    "is", "are", "was", "were", "be", "being", "been", "the", "a", "an", "in", "on", "at", "of",
    "for", "with", "by", "to", "from", "that", "this", "these", "those", "it", "its", "as"
}


def normalize_claim(claim: str) -> str:
    cleaned = claim.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"[’‘`\"]", "'", cleaned)
    return cleaned


def extract_keywords(claim: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", claim)
    keywords = [token for token in tokens if token.lower() not in stopwords]
    return keywords[:12]


def analyze_claim(claim: str) -> Dict[str, List[str]]:
    normalized = normalize_claim(claim)
    keywords = extract_keywords(normalized)
    return {
        "claim": normalized,
        "keywords": keywords,
    }
