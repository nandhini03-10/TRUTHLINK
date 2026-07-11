import logging
import math
import os
from typing import Optional

try:
    import openai
    OPENAI_IMPORTED = True
except ImportError:
    OPENAI_IMPORTED = False

try:
    from transformers import AutoModel, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None
_tokenizer = None

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_AVAILABLE = OPENAI_IMPORTED and bool(OPENAI_API_KEY)
if OPENAI_AVAILABLE:
    openai.api_key = OPENAI_API_KEY


def _load_model() -> None:
    global _model, _tokenizer
    if not TRANSFORMERS_AVAILABLE:
        return
    if _model is None or _tokenizer is None:
        try:
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            _model = AutoModel.from_pretrained(MODEL_NAME)
            _model.eval()
        except Exception as exc:
            logging.warning("Failed to load transformers model: %s", exc)
            _model = None
            _tokenizer = None


def _mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


def _openai_embed_text(text: str):
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI API key not configured or openai package not installed")
    try:
        response = openai.Embedding.create(model="text-embedding-3-small", input=text)
        return response["data"][0]["embedding"]
    except Exception as exc:
        logging.warning("OpenAI embedding failed: %s", exc)
        raise


def _embed_text(text: str):
    if OPENAI_AVAILABLE:
        return _openai_embed_text(text)
    if not TRANSFORMERS_AVAILABLE:
        raise RuntimeError("No local or OpenAI embedding available")
    _load_model()
    if _model is None or _tokenizer is None:
        raise RuntimeError("Model loading failed")
    encoded = _tokenizer(text, truncation=True, padding=True, return_tensors="pt", max_length=256)
    with torch.no_grad():
        model_output = _model(**encoded)
    embedding = _mean_pooling(model_output, encoded["attention_mask"])
    return embedding[0].cpu().numpy().tolist()


POSITIVE_FILM_TERMS = {
    "hit", "blockbuster", "success", "superhit", "smash", "record", "record-breaking", "rosy", "crowd-puller",
    "box office success", "box office hit", "went on to gross", "grossed", "earned", "revenue", "collection"
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


def _cosine_similarity(a, b) -> float:
    if hasattr(a, "tolist"):
        a = list(a)
    if hasattr(b, "tolist"):
        b = list(b)
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def compute_similarity(claim: str, text: str) -> float:
    claim_text = claim.strip()
    text = text.strip()
    if not claim_text or not text:
        return 0.0
    if TRANSFORMERS_AVAILABLE:
        try:
            claim_emb = _embed_text(claim_text)
            text_emb = _embed_text(text)
            return max(0.0, min(1.0, _cosine_similarity(claim_emb, text_emb)))
        except Exception:
            return _keyword_similarity(claim_text, text)
    return _keyword_similarity(claim_text, text)


def _keyword_similarity(claim: str, text: str) -> float:
    claim_words = [word.lower() for word in claim.split() if len(word) >= 3]
    text_lower = text.lower()
    if not claim_words:
        return 0.0
    matches = sum(1 for word in claim_words if word in text_lower)
    return min(1.0, matches / max(1, len(claim_words)))


def validate_source(claim: str, title: str, text: str, entities: dict) -> int:
    match_text = f"{title}\n{text}"
    similarity = compute_similarity(claim, match_text)
    entity_match = any(entity.lower() in match_text.lower() for entity_list in entities.values() for entity in entity_list)
    score = int(round(similarity * 100))

    claim_polarity = _determine_polarity(claim)
    text_polarity = _determine_polarity(match_text)
    if claim_polarity != 0 and text_polarity != 0 and claim_polarity != text_polarity:
        # Contradictory evidence should not support the claim
        return 10

    if claim_polarity != 0 and text_polarity == 0 and similarity < 0.55:
        # Neutral evidence should not strongly support a polarity-specific claim.
        return 10

    if entity_match:
        score = max(score, 40)
    if similarity >= 0.7 and entity_match:
        return min(100, max(score, 90))
    if similarity >= 0.5 and entity_match:
        return min(100, max(score, 70))
    if entity_match and score >= 40:
        return min(100, max(score, 50))
    return score
