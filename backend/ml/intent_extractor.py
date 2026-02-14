# backend/ml/intent_extractor.py
"""
Intent Extractor using Ollama LLM
Validates and extracts core civic issue from user input
"""

import requests
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT = """You are given a civic complaint.

If the text is meaningless, gibberish, unrelated to civic issues,
or does not describe a real-world public problem, respond ONLY with:
INVALID

Otherwise, rewrite the complaint as ONE short sentence describing
ONLY the core civic issue.

Ignore:
- addresses
- directions
- urgency words
- emotions
- contact details

Give more importance to that main issue and ignore consequences.
Do NOT mention departments.
Do NOT add new information.

Complaint:
{complaint}
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