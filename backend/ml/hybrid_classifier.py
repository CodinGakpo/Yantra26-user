"""
Hybrid classifier that combines image and text classification

FINAL FIX:
- Always returns a `reason` field
- Fully compatible with views.py
- No logic changes, only schema consistency
"""

from .text_router import route_issue


def hybrid_classify(
    image_department: str,
    image_confidence: float,
    title: str,
    description: str,
    image_threshold: float = 0.45
) -> dict:

    print("\n🔀 HYBRID CLASSIFY")
    print(f"   Image: {image_department} ({image_confidence:.3f})")

    HIGH_CONFIDENCE_THRESHOLD = 1.0

    # --------------------------------------------------
    # Strategy 1: Trust image if VERY high confidence
    # --------------------------------------------------
    if image_confidence >= HIGH_CONFIDENCE_THRESHOLD and image_department != "Manual":
        return {
            "final_department": image_department,
            "confidence": image_confidence,
            "method": "IMAGE_ONLY",
            "reason": "Very high confidence image classification",
            "image_result": {
                "department": image_department,
                "confidence": image_confidence
            }
        }

    # --------------------------------------------------
    # Strategy 2: Always try text classification
    # --------------------------------------------------
    text_result = route_issue(title, description)

    # Ollama unavailable
    if text_result["status"] == "OLLAMA_ERROR":
        if image_confidence >= image_threshold and image_department != "Manual":
            return {
                "final_department": image_department,
                "confidence": image_confidence,
                "method": "IMAGE_FALLBACK",
                "reason": "Text classification unavailable, using image result",
                "image_result": {
                    "department": image_department,
                    "confidence": image_confidence
                },
                "text_result": text_result
            }

        return {
            "final_department": "Manual",
            "confidence": 0.0,
            "method": "MANUAL_FALLBACK",
            "reason": "Text classification failed and image confidence too low",
            "text_result": text_result
        }

    # Invalid text
    if text_result["status"] == "INVALID":
        if image_confidence >= image_threshold and image_department != "Manual":
            return {
                "final_department": image_department,
                "confidence": image_confidence,
                "method": "IMAGE_ONLY",
                "reason": "Text input invalid, using image classification",
                "image_result": {
                    "department": image_department,
                    "confidence": image_confidence
                },
                "text_result": text_result
            }

        return {
            "final_department": "Manual",
            "confidence": 0.0,
            "method": "MANUAL",
            "reason": "Invalid text and low confidence image",
            "text_result": text_result
        }

    # --------------------------------------------------
    # Strategy 3: Text routed successfully
    # --------------------------------------------------
    if text_result["status"] == "ROUTED":
        text_dept = text_result["department"]
        text_conf = text_result["confidence"]

        print(f"   → Text: {text_dept} ({text_conf:.3f})")

        # Agreement
        if text_dept == image_department:
            return {
                "final_department": text_dept,
                "confidence": (image_confidence + text_conf) / 2,
                "method": "HYBRID_AGREEMENT",
                "reason": "Image and text classification agree",
                "image_result": {
                    "department": image_department,
                    "confidence": image_confidence
                },
                "text_result": text_result
            }

        # Disagreement → Manual
        return {
            "final_department": "Manual",
            "confidence": 0.0,
            "method": "REJECTED_MISMATCH",
            "reason": f"Image and text disagree (Image: {image_department}, Text: {text_dept})",
            "image_result": {
                "department": image_department,
                "confidence": image_confidence
            },
            "text_result": text_result
        }

    # --------------------------------------------------
    # Strategy 4: Text out of scope
    # --------------------------------------------------
    if text_result["status"] == "OUT_OF_SCOPE":
        
        return {
            "final_department": "Manual",
            "confidence": 0.0,
            "method": "MANUAL",
            "reason": "Both image and text classifications uncertain",
            "text_result": text_result
        }

    # --------------------------------------------------
    # Final fallback (should never happen)
    # --------------------------------------------------
    return {
        "final_department": "Manual",
        "confidence": 0.0,
        "method": "MANUAL_FALLBACK",
        "reason": "Unexpected classification state",
        "image_result": {
            "department": image_department,
            "confidence": image_confidence
        },
        "text_result": text_result
    }
