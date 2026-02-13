import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT = """
You are given a civic complaint.

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

Do NOT mention departments.
Do NOT add new information.

Complaint:
{complaint}
"""

def extract_intent_or_invalid(title: str, description: str) -> str:
    complaint = f"{title}\n{description}".strip()

    r = requests.post(
        OLLAMA_URL,
        json={
            "model": "qwen2.5:1.5b-instruct",
            "prompt": PROMPT.format(complaint=complaint),
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=5
    )
    r.raise_for_status()
    return r.json()["response"].strip()
