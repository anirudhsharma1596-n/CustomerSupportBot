# TechCorp Support Bot

A customer support bot that returns **consistent, structured JSON answers** for every question — no matter how it's phrased. Built to explore context engineering, system prompt design, and output format enforcement with the OpenAI API.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red) ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green)

---

## What it does

- Accepts any natural language support question
- Always returns a structured JSON response with fixed fields: `intent`, `confidence`, `answer`, `steps`, `escalate`, `escalate_reason`, `related_topics`
- Classifies questions into 5 intent categories: `billing`, `technical`, `account`, `refund`, `general`
- Automatically escalates billing disputes and account suspension issues
- Scores live consistency of each answer against previous answers of the same intent
- Logs every Q&A to a persistent JSON file
- Displays everything in a clean Streamlit chat interface

---

## Demo

```
Q: What is your refund policy?
Q: Can I get a refund?
Q: Is there a money-back guarantee?

All three return → intent: refund | answer: "Full refund within 14 days of payment, no questions asked."
Consistency score: 100%
```

---

## Project structure

```
qa_bot/
├── system_prompt.py       # the engineered system prompt — role, schema, rules, knowledge
├── bot.py                 # core ask_bot() function — API call, JSON parsing, validation
├── logger.py              # persistent logging + live consistency scoring
├── app.py                 # Streamlit UI
├── test_api.py            # basic API connection test
├── test_prompt.py         # quick 3-question prompt verification
├── test_consistency.py    # 22-question consistency test across 3 groups
├── requirements.txt       # dependencies
└── .env.example           # environment variable template
```

---

## Quickstart

### 1. Clone and set up environment

```bash
git clone https://github.com/YOUR_USERNAME/qa-bot.git
cd qa-bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add your API key

```bash
cp .env.example .env
# Open .env and add your key:
# OPENAI_API_KEY=your_key_here
```

Get your key at [platform.openai.com](https://platform.openai.com) → API Keys.

### 3. Run the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

### 4. Run consistency tests

```bash
python test_consistency.py
```

Tests 22 question variations across 3 groups and saves results to `consistency_log.json`.

---

## Consistency results

After 3 rounds of prompt tuning:

| Group            | Similarity | Intent agreement | Escalation agreement |
|------------------|-----------|-----------------|---------------------|
| refund_policy    | 1.000     | 100%            | 100%                |
| reset_password   | 1.000     | 100%            | 100%                |
| billing_dispute  | 0.773     | 100%            | 100%                |
| **Overall avg**  | **0.924** | **100%**        | **100%**            |

---

## How it works

### Context Engineering

The consistency of this bot comes entirely from how the system prompt is designed — not from any special model capability. The prompt has four layers:

**Role** — sets who the bot is and what company it serves.

**Output schema** — defines the exact JSON structure the model must always return. Showing the model a schema is far more reliable than describing it in prose.

**Rules** — explicit constraints for every field. Critically, rules use anchor templates for high-consistency fields. Example:
```
For password/login questions: ALWAYS use this exact sentence:
"To reset your password, go to the login page, click 'Forgot password',
enter your email, and check your inbox for the reset link."
```

**Grounding knowledge** — company facts (plans, pricing, policies) so the model never guesses.

### Prompt tuning process

1. Run `test_consistency.py` → get similarity scores per group
2. Find the lowest scoring group → read the actual answers to diagnose why
3. Add a more specific rule or anchor template → re-run all groups
4. Repeat until all groups score above 0.70

Key insight: **tuning one group can hurt another**. Always re-run everything after each change.

---

## API response schema

Every response follows this exact structure:

```json
{
  "intent": "refund",
  "confidence": 1.0,
  "answer": "Full refund within 14 days of payment, no questions asked.",
  "steps": [],
  "escalate": false,
  "escalate_reason": "",
  "related_topics": ["cancellation", "billing", "subscription"]
}
```

---

## Requirements

```
openai
streamlit
python-dotenv
```

---

## Environment variables

| Variable         | Description              |
|------------------|--------------------------|
| `OPENAI_API_KEY` | Your OpenAI API key      |

---

## What I learned building this

- **Context engineering** is the practice of deliberately designing everything in the LLM's context window — role, rules, output format, and grounding knowledge
- `temperature=0.1` is essential for consistency — high temperature = creative but variable
- Anchor templates (exact sentences in the prompt) produce similarity scores near 1.0
- JSON schema enforcement in the system prompt is far more reliable than asking for "structured output" in prose
- Streamlit's rerun model + `session_state` is the key pattern for building stateful AI apps

---

## License

MIT