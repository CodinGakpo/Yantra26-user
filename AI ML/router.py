import numpy as np
from sentence_transformers import SentenceTransformer
from intent_extractor import extract_intent_or_invalid


DEPARTMENTS = {
    0: "Garbage Department: waste, garbage, trash, dumping, cleanliness issues",
    1: "Public Works Department: road damage, potholes, broken infrastructure",
    2: "Traffic Department: traffic signals, congestion, parking, road safety",
    3: "Vandalism Department: graffiti, defacement, damage to public property",
    4: "Water Board Department: water leakage, pipe burst, sewage, drainage",
    5: "Missing Persons Department: lost person, missing child, elderly, animals"
}


embedder = SentenceTransformer("all-MiniLM-L6-v2")

DEPT_TEXTS = list(DEPARTMENTS.values())
DEPT_IDS = list(DEPARTMENTS.keys())
DEPT_EMBEDS = embedder.encode(
    DEPT_TEXTS,
    normalize_embeddings=True
)

MIN_CONFIDENCE = 0.45
MIN_MARGIN = 0.05


def route_issue(title: str, description: str):
    
    intent = extract_intent_or_invalid(title, description)

    if intent.upper() == "INVALID":
        return {
            "status": "INVALID",
            "reason": "Input is not a valid civic issue"
        }


    intent_embed = embedder.encode(
        intent,
        normalize_embeddings=True
    )

    sims = np.dot(DEPT_EMBEDS, intent_embed)

    best_idx = int(np.argmax(sims))
    best_score = float(sims[best_idx])

    sorted_sims = np.sort(sims)
    margin = sorted_sims[-1] - sorted_sims[-2]

    if best_score < MIN_CONFIDENCE or margin < MIN_MARGIN:
        return {
            "status": "OUT_OF_SCOPE",
            "reason": "No confident department match",
            "intent": intent,
            "scores": dict(zip(DEPT_IDS, sims.round(3)))
        }

    return {
        "status": "ROUTED",
        "department_id": DEPT_IDS[best_idx],
        "department": DEPARTMENTS[DEPT_IDS[best_idx]].split(":")[0],
        "confidence": round(best_score, 3),
        "intent": intent
    }






print(1)
print(route_issue(
    "big potholes clear urgent",
    "near bus stop opposite temple"
))


print(2)
print(route_issue(
    "asdf qwer zxcv",
    "123 !!!"
))


print(3)
print(route_issue(
    "my dog is missing",
    "please help"
))
