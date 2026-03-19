import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from system_prompt import SYSTEM_PROMPT

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask(question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=512,
        temperature=0.1,        # low = more consistent, less random
        messages=[
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": question}
        ]
    )
    raw = response.choices[0].message.content
    return raw

# --- Test with 3 different questions ---
test_questions = [
    "I want my refund. When will I get?",
    "I want to change password",
    "I was charged twice this month!"
]

for q in test_questions:
    print(f"\nQ: {q}")
    print("-" * 50)
    raw = ask(q)

    # Try to parse it as JSON
    try:
        parsed = json.loads(raw)
        print("JSON valid!")
        print(f"  intent   : {parsed['intent']}")
        print(f"  answer   : {parsed['answer']}")
        print(f"  escalate : {parsed['escalate']}")
    except json.JSONDecodeError:
        print("INVALID JSON — raw output was:")
        print(raw)

