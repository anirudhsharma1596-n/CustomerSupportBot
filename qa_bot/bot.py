import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from system_prompt import SYSTEM_PROMPT

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# These are the exact keys we expect in every response
REQUIRED_KEYS = {"intent", "confidence", "answer", "steps", "escalate", "escalate_reason", "related_topics"}

# Valid values for the intent field
VALID_INTENTS = {"billing", "technical", "account", "refund", "general"}


def validate_response(parsed: dict) -> tuple[bool, str]:
    """
    Check that the parsed JSON has all required keys and valid values.
    Returns (is_valid, error_message).
    """
    # Check all required keys exist
    missing = REQUIRED_KEYS - parsed.keys()
    if missing:
        return False, f"Missing keys: {missing}"

    # Check intent is one of the allowed values
    if parsed["intent"] not in VALID_INTENTS:
        return False, f"Invalid intent: '{parsed['intent']}'"

    # Check confidence is a number between 0 and 1
    if not isinstance(parsed["confidence"], (int, float)):
        return False, "confidence must be a number"
    if not (0.0 <= parsed["confidence"] <= 1.0):
        return False, f"confidence out of range: {parsed['confidence']}"

    # Check escalate is a boolean
    if not isinstance(parsed["escalate"], bool):
        return False, "escalate must be true or false"

    # Check steps and related_topics are lists
    if not isinstance(parsed["steps"], list):
        return False, "steps must be a list"
    if not isinstance(parsed["related_topics"], list):
        return False, "related_topics must be a list"

    return True, ""


def ask_bot(question: str, temperature: float = 0.1) -> dict:
    """
    Send a question to the bot and return a structured result dict.

    Always returns a dict with these keys:
        success    : bool   — did we get a valid response?
        data       : dict   — the parsed JSON from the model (empty if failed)
        raw        : str    — the raw text the model returned
        error      : str    — error message if success is False
        latency    : float  — how many seconds the API call took
    """
    start_time = time.time()

    try:
        # --- Make the API call ---
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=512,
            temperature=temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": question}
            ]
        )
        raw = response.choices[0].message.content.strip()

    except Exception as e:
        # API call itself failed (network error, invalid key, etc.)
        return {
            "success": False,
            "data":    {},
            "raw":     "",
            "error":   f"API error: {str(e)}",
            "latency": round(time.time() - start_time, 2)
        }

    # --- Try to parse the raw text as JSON ---
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "success": False,
            "data":    {},
            "raw":     raw,
            "error":   "Model returned invalid JSON",
            "latency": round(time.time() - start_time, 2)
        }

    # --- Validate the parsed JSON has correct structure ---
    is_valid, error_msg = validate_response(parsed)
    if not is_valid:
        return {
            "success": False,
            "data":    parsed,
            "raw":     raw,
            "error":   f"Validation failed: {error_msg}",
            "latency": round(time.time() - start_time, 2)
        }

    # --- All good ---
    return {
        "success": True,
        "data":    parsed,
        "raw":     raw,
        "error":   "",
        "latency": round(time.time() - start_time, 2)
    }


# ── Quick test when you run this file directly ────────────────────────────────
if __name__ == "__main__":
    questions = [
        "What is your refund policy?",
        "How do I reset my password?",
        "I was charged twice this month!",
        "What storage do I get on the free plan?",
    ]

    for q in questions:
        print(f"\n{'='*55}")
        print(f"Q: {q}")
        result = ask_bot(q)

        if result["success"]:
            d = result["data"]
            print(f"  intent    : {d['intent']}")
            print(f"  confidence: {d['confidence']}")
            print(f"  answer    : {d['answer']}")
            print(f"  steps     : {d['steps']}")
            print(f"  escalate  : {d['escalate']}")
            if d["escalate"]:
                print(f"  reason    : {d['escalate_reason']}")
            print(f"  related   : {d['related_topics']}")
            print(f"  latency   : {result['latency']}s")
        else:
            print(f"  FAILED: {result['error']}")
            print(f"  raw output was: {result['raw']}")