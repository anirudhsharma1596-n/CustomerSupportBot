import json
import os
from datetime import datetime
from difflib import SequenceMatcher

LOG_FILE = "chat_log.json"


def load_log() -> list:
    """Load existing log from file. Returns empty list if file doesn't exist."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)


def save_log(entries: list):
    """Write the full log list back to file."""
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def append_entry(question: str, result: dict):
    """
    Append one Q&A entry to the log file.
    Called every time the bot gives a successful response.
    """
    entries = load_log()
    entries.append({
        "timestamp": datetime.now().isoformat(),
        "question":  question,
        "intent":    result["data"].get("intent", ""),
        "answer":    result["data"].get("answer", ""),
        "escalate":  result["data"].get("escalate", False),
        "latency":   result["latency"]
    })
    save_log(entries)


def similarity(a: str, b: str) -> float:
    """Return 0.0–1.0 similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def consistency_score(current_answer: str, intent: str) -> dict:
    """
    Compare current_answer against all previous answers with the same intent.
    Returns a dict with score and how many answers were compared against.
    """
    entries = load_log()

    # Get all past answers for this intent (excluding the current one we just saved)
    past_answers = [
        e["answer"] for e in entries
        if e["intent"] == intent and e["answer"] != current_answer
    ]

    if not past_answers:
        return {"score": None, "compared_against": 0}

    scores = [similarity(current_answer, past) for past in past_answers]
    avg    = round(sum(scores) / len(scores), 3)
    return {"score": avg, "compared_against": len(past_answers)}