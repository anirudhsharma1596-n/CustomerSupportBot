import streamlit as st
from openai import OpenAI
from bot import ask_bot, validate_response
from logger import append_entry, consistency_score, load_log
from system_prompt import SYSTEM_PROMPT
import json

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TechCorp Support Bot",
    page_icon="🤖",
    layout="wide"
)

# ── Cache the OpenAI client ───────────────────────────────────────────────────
# @st.cache_resource creates the client ONCE and reuses it across all reruns.
# Without this, a new client object would be created on every single interaction.
@st.cache_resource
def get_client():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

client = get_client()

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ── Intent badge colors ───────────────────────────────────────────────────────
INTENT_COLORS = {
    "billing":   "#FAC775",
    "technical": "#85B7EB",
    "account":   "#9FE1CB",
    "refund":    "#F0997B",
    "general":   "#D3D1C7",
}

def intent_badge(intent: str) -> str:
    color = INTENT_COLORS.get(intent, "#D3D1C7")
    return (
        f"<span style='background:{color};padding:3px 12px;"
        f"border-radius:12px;font-size:13px;font-weight:500'>"
        f"{intent.upper()}</span>"
    )

# ── Consistency score badge ───────────────────────────────────────────────────
def score_badge(score: float) -> str:
    if score >= 0.85:
        color, label = "#9FE1CB", "consistent"
    elif score >= 0.65:
        color, label = "#FAC775", "moderate"
    else:
        color, label = "#F0997B", "inconsistent"
    return (
        f"<span style='background:{color};padding:3px 10px;"
        f"border-radius:12px;font-size:12px'>"
        f"consistency: {score:.0%} ({label})</span>"
    )

# ── Render one response card ──────────────────────────────────────────────────
def render_response(question: str, result: dict, c_score: dict):
    if not result["success"]:
        st.error(f"Error: {result['error']}")
        return

    d = result["data"]

    # Question bubble
    st.markdown(
        f"<div style='background:#f0f2f6;border-radius:12px;"
        f"padding:12px 16px;margin-bottom:12px;font-size:15px'>"
        f"<strong>You:</strong> {question}</div>",
        unsafe_allow_html=True
    )

    # Intent + confidence + consistency row
    col1, col2 = st.columns([3, 1])
    with col1:
        badge_html = intent_badge(d["intent"])
        if c_score["score"] is not None:
            badge_html += "&nbsp;&nbsp;" + score_badge(c_score["score"])
        st.markdown(badge_html, unsafe_allow_html=True)
    with col2:
        st.markdown(
            f"<p style='text-align:right;color:gray;font-size:13px;margin:0'>"
            f"confidence: {d['confidence']:.0%} · {result['latency']}s</p>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Answer
    st.markdown("**Answer**")
    st.write(d["answer"])

    # Steps
    if d["steps"]:
        st.markdown("**Steps**")
        for i, step in enumerate(d["steps"], 1):
            st.markdown(f"{i}. {step}")

    # Escalation
    if d["escalate"]:
        st.warning(f"Escalated to support team — {d['escalate_reason']}")

    # Related topics
    if d["related_topics"]:
        topics_html = " ".join([
            f"<span style='background:#eee;padding:2px 10px;"
            f"border-radius:10px;font-size:12px;margin-right:4px'>{t}</span>"
            for t in d["related_topics"]
        ])
        st.markdown(f"**Related:** {topics_html}", unsafe_allow_html=True)

    # Raw JSON expander — useful for debugging and learning
    with st.expander("View raw JSON response"):
        st.json(d)

    st.markdown("---")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### TechCorp Support Bot")
    st.caption("Powered by GPT-4o-mini")
    st.markdown("---")

    # Live stats from the persistent log
    st.markdown("### Session stats")
    all_entries = load_log()
    total       = len(all_entries)
    escalated   = sum(1 for e in all_entries if e.get("escalate"))
    if total > 0:
        avg_latency = round(sum(e["latency"] for e in all_entries) / total, 2)
        intent_counts = {}
        for e in all_entries:
            intent_counts[e["intent"]] = intent_counts.get(e["intent"], 0) + 1
        top_intent = max(intent_counts, key=intent_counts.get)
    else:
        avg_latency = 0
        top_intent  = "—"

    col1, col2 = st.columns(2)
    col1.metric("Total questions", total)
    col2.metric("Escalated", escalated)
    col1.metric("Avg latency", f"{avg_latency}s")
    col2.metric("Top intent", top_intent)

    st.markdown("---")

    # Session history
    st.markdown("### History")
    if not st.session_state.history:
        st.caption("No questions yet.")
    else:
        for entry in reversed(st.session_state.history):
            q   = entry["question"]
            res = entry["result"]
            label = q if len(q) <= 38 else q[:35] + "..."
            if res["success"]:
                color = INTENT_COLORS.get(res["data"]["intent"], "#ccc")
                st.markdown(
                    f"<div style='padding:6px 8px;border-left:3px solid {color};"
                    f"margin-bottom:6px;font-size:13px'>{label}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='padding:6px 8px;border-left:3px solid red;"
                    f"margin-bottom:6px;font-size:13px;color:red'>{label}</div>",
                    unsafe_allow_html=True
                )

    st.markdown("---")
    if st.button("Clear session"):
        st.session_state.history = []
        st.rerun()


# ── Main area ─────────────────────────────────────────────────────────────────
st.title("TechCorp Support Bot")
st.caption("Ask any support question — structured, consistent answers every time.")

question = st.chat_input("Type your question here...")

if question:
    with st.spinner("Thinking..."):
        result = ask_bot(question)

    # Save to persistent log and compute consistency
    c_score = {"score": None, "compared_against": 0}
    if result["success"]:
        append_entry(question, result)
        c_score = consistency_score(
            result["data"]["answer"],
            result["data"]["intent"]
        )

    # Save to session history
    st.session_state.history.append({
        "question": question,
        "result":   result,
        "c_score":  c_score
    })

# Render responses
if st.session_state.history:
    for entry in reversed(st.session_state.history):
        render_response(
            entry["question"],
            entry["result"],
            entry.get("c_score", {"score": None, "compared_against": 0})
        )
else:
    st.markdown("### Try asking:")
    for ex in [
        "What is your refund policy?",
        "How do I reset my password?",
        "I was charged twice this month!",
        "What storage do I get on the free plan?",
        "How do I cancel my subscription?",
    ]:
        st.markdown(f"- *{ex}*")