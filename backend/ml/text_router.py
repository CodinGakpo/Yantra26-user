"""
Text-based department router using sentence embeddings
FIXED: Index-safe mapping, CNN-compatible output
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from .intent_extractor import extract_intent_or_invalid

DEPARTMENTS = {
    0: "Garbage Department: waste, garbage, trash, dumping, cleanliness issues",
    1: "Public Works Department: road damage, potholes, broken infrastructure",
    2: "Traffic Department: traffic signals, congestion, parking, road safety",
    3: "Vandalism Department: graffiti, defacement, damage to public property",
    4: "Water Board Department: water leakage, pipe burst, sewage, drainage",
    5: "Missing Persons Department: lost person, missing child, elderly, animals"
}

DEPT_NAME_MAPPING = {
    0: "Garbage Department",
    1: "Public Works Department",
    2: "Traffic Department",
    3: "Vandalism Department",
    4: "Water Board Department",
    5: "Missing Persons Department"
}

MIN_CONFIDENCE = 0.35
MIN_MARGIN = 0.05

_embedder = None
_dept_embeds = None


def get_embedder():
    global _embedder, _dept_embeds

    if _embedder is None:
        print("Loading sentence-transformers model...")
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")

        dept_texts = list(DEPARTMENTS.values())
        _dept_embeds = _embedder.encode(
            dept_texts,
            normalize_embeddings=True
        )

        print("✓ Embedder loaded & department embeddings cached")

    return _embedder, _dept_embeds


def route_issue(title: str, description: str) -> dict:
    print("\n TEXT ROUTING")
    print(f"   Title: {title[:50]}")
    print(f"   Desc : {description[:50]}")

    intent = extract_intent_or_invalid(title, description)

    if intent is None:
        return {
            "status": "OLLAMA_ERROR",
            "department": None,
            "confidence": 0.0
        }

    if intent.upper() == "INVALID":
        return {
            "status": "INVALID",
            "department": None,
            "confidence": 0.0,
            "intent": intent
        }

    embedder, dept_embeds = get_embedder()

    intent_embed = embedder.encode(
        intent,
        normalize_embeddings=True
    )

    similarities = np.dot(dept_embeds, intent_embed)

    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])

    sorted_sims = np.sort(similarities)
    margin = sorted_sims[-1] - sorted_sims[-2]

    department_name = DEPT_NAME_MAPPING[best_idx]

    scores = {
        DEPT_NAME_MAPPING[i]: float(similarities[i])
        for i in range(len(similarities))
    }

    print(f"   → Best: {department_name} ({best_score:.3f}, margin {margin:.3f})")

    if best_score < MIN_CONFIDENCE or margin < MIN_MARGIN:
        return {
            "status": "OUT_OF_SCOPE",
            "department": None,
            "confidence": best_score,
            "intent": intent,
            "scores": scores
        }

    return {
        "status": "ROUTED",
        "department": department_name, 
        "department_id": best_idx,
        "confidence": round(best_score, 3),
        "intent": intent,
        "scores": scores
    }
