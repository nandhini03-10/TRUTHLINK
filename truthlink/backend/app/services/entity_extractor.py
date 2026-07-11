from typing import Dict, List

known_companies = ["Tesla", "Microsoft", "Google", "Apple", "Amazon", "Meta"]
known_locations = ["India", "USA", "United States", "Europe", "China", "UK"]
known_people = ["Elon Musk", "Sundar Pichai", "Tim Cook", "Satya Nadella"]


def extract_entities(claim: str) -> Dict[str, List[str]]:
    lower = claim.lower()
    companies = [name for name in known_companies if name.lower() in lower]
    locations = [name for name in known_locations if name.lower() in lower]
    people = [name for name in known_people if name.lower() in lower]
    return {
        "company": companies,
        "location": locations,
        "person": people,
    }
