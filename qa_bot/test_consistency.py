import json
import time
from datetime import datetime
from difflib import SequenceMatcher
from bot import ask_bot

# ── Question variations ───────────────────────────────────────────────────────
# Same underlying question asked 20+ different ways.
# Goal: all should produce the same intent, escalate value, and similar answer.

VARIATION_GROUPS = {
    "refund_policy": [
        "What is your refund policy?",
        "Can I get a refund?",
        "How do I get my money back?",
        "Do you offer refunds?",
        "I want to cancel and get a refund",
        "What happens if I want my money back?",
        "Is there a money back guarantee?",
        "How long do I have to request a refund?",
    ],
    "reset_password": [
        "How do I reset my password?",
        "I forgot my password",
        "Can't log in, what do I do?",
        "How do I recover my account?",
        "I lost access to my account",
        "Password reset steps?",
        "How to change my password?",
        "I can't remember my password",
    ],
    "billing_dispute": [
        "I was charged twice this month!",
        "You charged me incorrectly",
        "There's a wrong charge on my account",
        "I see an unexpected payment",
        "I was billed the wrong amount",
        "Why was I charged again?",
    ],
}


# ── Similarity scoring ────────────────────────────────────────────────────────

def similarity_score(a: str, b: str) -> float:
    """Return a 0.0–1.0 similarity score between two strings."""
    return round(SequenceMatcher(None, a.lower(), b.lower()).ratio(), 3)


def average_similarity(answers: list[str]) -> float:
    """
    Compare every answer against every other answer and return the average score.
    A score of 1.0 means all answers are identical.
    A score above 0.7 is generally good for a support bot.
    """
    if len(answers) < 2:
        return 1.0
    scores = []
    for i in range(len(answers)):
        for j in range(i + 1, len(answers)):
            scores.append(similarity_score(answers[i], answers[j]))
    return round(sum(scores) / len(scores), 3)


# ── Run tests for one group ───────────────────────────────────────────────────

def test_group(group_name: str, questions: list[str]) -> dict:
    """
    Ask all questions in a group, collect results, and compute consistency metrics.
    Returns a summary dict for this group.
    """
    print(f"\n{'='*60}")
    print(f"Testing group: '{group_name}' ({len(questions)} variations)")
    print(f"{'='*60}")

    results      = []
    answers      = []
    intents      = []
    escalations  = []
    failed       = 0

    for i, question in enumerate(questions, 1):
        print(f"  [{i}/{len(questions)}] {question[:55]}...")
        result = ask_bot(question)
        time.sleep(0.5)   # small delay to avoid hitting rate limits

        if result["success"]:
            d = result["data"]
            answers.append(d["answer"])
            intents.append(d["intent"])
            escalations.append(d["escalate"])
            results.append({
                "question":   question,
                "success":    True,
                "intent":     d["intent"],
                "confidence": d["confidence"],
                "answer":     d["answer"],
                "escalate":   d["escalate"],
                "latency":    result["latency"]
            })
        else:
            failed += 1
            results.append({
                "question": question,
                "success":  False,
                "error":    result["error"]
            })

    # ── Compute metrics ───────────────────────────────────────────────────────
    total       = len(questions)
    success     = total - failed
    avg_sim     = average_similarity(answers) if answers else 0.0
    # What % of responses agreed on intent?
    top_intent  = max(set(intents), key=intents.count) if intents else "n/a"
    intent_agree = round(intents.count(top_intent) / success, 3) if success else 0
    # What % agreed on escalation?
    top_escalate = max(set(escalations), key=escalations.count) if escalations else None
    esc_agree    = round(escalations.count(top_escalate) / success, 3) if success else 0

    summary = {
        "group":              group_name,
        "total_questions":    total,
        "successful":         success,
        "failed":             failed,
        "avg_answer_similarity": avg_sim,
        "dominant_intent":    top_intent,
        "intent_agreement":   intent_agree,
        "escalation_agreement": esc_agree,
        "results":            results
    }

    # ── Print group report ────────────────────────────────────────────────────
    print(f"\n  Results for '{group_name}':")
    print(f"    Successful responses : {success}/{total}")
    print(f"    Answer similarity    : {avg_sim}  (target: >0.70)")
    print(f"    Intent agreement     : {intent_agree*100:.0f}%  (dominant: {top_intent})")
    print(f"    Escalation agreement : {esc_agree*100:.0f}%")

    if avg_sim >= 0.80:
        print("    Consistency: EXCELLENT")
    elif avg_sim >= 0.65:
        print("    Consistency: GOOD — minor tuning may help")
    else:
        print("    Consistency: NEEDS WORK — review system prompt rules")

    return summary


# ── Main ──────────────────────────────────────────────────────────────────────

def run_all():
    print("Starting consistency tests...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_summaries = []

    for group_name, questions in VARIATION_GROUPS.items():
        summary = test_group(group_name, questions)
        all_summaries.append(summary)

    # ── Save full log to JSON file ────────────────────────────────────────────
    log = {
        "run_at":    datetime.now().isoformat(),
        "summaries": all_summaries
    }
    with open("consistency_log.json", "w") as f:
        json.dump(log, f, indent=2)
    print("\nFull log saved to consistency_log.json")

    # ── Final report ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("FINAL REPORT")
    print(f"{'='*60}")
    for s in all_summaries:
        print(f"  {s['group']:<20} similarity={s['avg_answer_similarity']}  intent={s['intent_agreement']*100:.0f}%")

    overall = round(
        sum(s["avg_answer_similarity"] for s in all_summaries) / len(all_summaries), 3
    )
    print(f"\n  Overall avg similarity: {overall}")


if __name__ == "__main__":
    run_all()