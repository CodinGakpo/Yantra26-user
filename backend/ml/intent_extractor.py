# backend/ml/intent_extractor.py
"""
Intent Extractor using Ollama LLM
Validates and extracts core civic issue from user input
"""

import requests
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT = """You are a civic complaint analyzer. Your job is to extract the core civic issue from user complaints.

RULES:
1. If the text is complete gibberish (random characters, no meaning), respond ONLY with: INVALID
2. If it describes a real civic/public infrastructure problem, extract the core issue as ONE short sentence
3. Remove addresses, directions, urgency words, emotions, and contact details
4. Do NOT mention department names in your response

Examples:

Complaint: "asdf qwer zxcv !!! 123"
Response: INVALID

Complaint: "Spillage... Water is leaking, diseases spread......"
Response: Water leakage causing spillage

Complaint: "Garbage on the road... Its dirty and not clean to sleep in"
Response: Garbage on the road

Complaint: "big potholes clear urgent near bus stop opposite temple"
Response: Large potholes need repair

Now analyze this complaint:

Complaint: {complaint}
Response:"""


def extract_intent_or_invalid(title: str, description: str, timeout: int = 10) -> Optional[str]:
    """
    Extract intent from complaint or return INVALID
    
    Args:
        title: Issue title
        description: Issue description
        timeout: Request timeout in seconds
        
    Returns:
        Extracted intent or "INVALID", or None if Ollama is unavailable
    """
    complaint = f"{title}\n{description}".strip()
    
    print(f"\nINTENT EXTRACTION:")
    print(f"   Input: '{complaint[:80]}...'")
    
    if not complaint:
        print(f"   → Empty input, returning INVALID")
        return "INVALID"
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen2.5:1.5b-instruct",
                "prompt": PROMPT.format(complaint=complaint),
                "stream": False,
                "options": {
                    "temperature": 0.3
                }
            },
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()["response"].strip()
        
        print(f"   → Ollama response: '{result}'")
        return result
        
    except requests.exceptions.Timeout:
        print(f"   →   Ollama request timed out after {timeout}s")
        return None
        
    except requests.exceptions.ConnectionError:
        print("   →  Cannot connect to Ollama. Make sure Ollama is running on localhost:11434")
        return None
        
    except Exception as e:
        print(f"   → Error extracting intent: {e}")
        return None