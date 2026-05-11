# backend/ml/intent_extractor.py
"""
Intent Extractor using Ollama LLM
Validates and extracts core civic issue from user input.
"""

import os
from typing import Optional

import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")

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


def _call_chat_endpoint(complaint: str, timeout: int) -> Optional[str]:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": PROMPT.format(complaint=complaint)}],
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=timeout,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()
    data = response.json()
    return (data.get("message", {}) or {}).get("content", "").strip()


def _call_generate_endpoint(complaint: str, timeout: int) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": PROMPT.format(complaint=complaint),
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def extract_intent_or_invalid(title: str, description: str, timeout: int = 20) -> Optional[str]:
    """
    Extract intent from complaint or return INVALID.

    Returns:
        Extracted intent or "INVALID", or None if Ollama is unavailable.
    """
    complaint = f"{title}\n{description}".strip()

    print("\nINTENT EXTRACTION:")
    print(f"   Input: '{complaint[:80]}...'")

    if not complaint:
        print("   -> Empty input, returning INVALID")
        return "INVALID"

    try:
        result = _call_chat_endpoint(complaint, timeout)
        if result is None:
            result = _call_generate_endpoint(complaint, timeout)

        print(f"   -> Ollama response: '{result}'")
        return result

    except requests.exceptions.Timeout:
        print(f"   -> Ollama request timed out after {timeout}s")
        return None

    except requests.exceptions.ConnectionError:
        print(f"   -> Cannot connect to Ollama at {OLLAMA_BASE_URL}")
        return None

    except Exception as e:
        print(f"   -> Error extracting intent: {e}")
        return None
