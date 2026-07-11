import re
from typing import Dict, List

known_companies = ["Tesla", "Microsoft", "Google", "Apple", "Amazon", "Meta"]
known_locations = ["India", "USA", "United States", "Europe", "China", "UK", "Burj Khalifa", "Dubai", "Salem"]
known_people = ["Elon Musk", "Sundar Pichai", "Tim Cook", "Satya Nadella", "Sivakarthikeyan", "Sivakumar Murugesan", "Jainam Jain", "Dhanush", "Suriya"]

GENERIC_TERMS = {
    "teenager", "actor", "actress", "star", "hero", "heroine", "film", "movie", "director", "producer",
    "startup", "company", "business", "student", "aspirant", "exam", "test", "suicide", "arrest",
    "next", "new", "latest", "today", "morning", "dubai", "burj", "khalifa"
}


def _find_proper_nouns(claim: str) -> List[str]:
    # Capture capitalized phrases and name-like terms from the claim
    phrases = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", claim)
    return [phrase for phrase in phrases if phrase.lower() not in GENERIC_TERMS]


def _find_lowercase_matches(claim: str, items: List[str]) -> List[str]:
    lower = claim.lower()
    return [item for item in items if item.lower() in lower]


def extract_entities(claim: str) -> Dict[str, List[str]]:
    lower = claim.lower()
    companies = _find_lowercase_matches(lower, known_companies)
    locations = _find_lowercase_matches(lower, known_locations)
    people = _find_lowercase_matches(lower, known_people)

    proper_nouns = _find_proper_nouns(claim)
    for phrase in proper_nouns:
        if phrase in known_locations and phrase not in locations:
            locations.append(phrase)
        elif phrase in known_people and phrase not in people:
            people.append(phrase)
        elif phrase not in locations and phrase not in people and phrase not in companies:
            if len(phrase.split()) >= 2:
                people.append(phrase)
            elif phrase.lower().endswith("kumar") or phrase.lower().endswith("murugesan"):
                people.append(phrase)
            elif phrase.lower() not in GENERIC_TERMS:
                companies.append(phrase)

    if "startup" in lower and not companies:
        companies.append("startup")
    if "ai" in lower and "startup" in lower and "AI startup" not in companies:
        companies.append("AI startup")
    if "burj khalifa" in lower and "Burj Khalifa" not in locations:
        locations.append("Burj Khalifa")

    return {
        "company": companies,
        "location": locations,
        "person": people,
    }
