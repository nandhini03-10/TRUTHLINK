from pydantic import BaseModel
from typing import List, Dict, Any

class VerifyRequest(BaseModel):
    claim: str

class StakeholderSource(BaseModel):
    name: str
    type: str
    url: str
    authority: int

class EvidenceItem(BaseModel):
    source: str
    kind: str
    text: str
    date: str
    authenticity: int
    relevance: int

class VerifyResponse(BaseModel):
    claim: str
    keywords: List[str]
    entities: Dict[str, List[str]]
    stakeholders: List[StakeholderSource]
    evidence: List[EvidenceItem]
    validation: Dict[str, int]
    truth_score: int
    classification: str
    explanation: str
