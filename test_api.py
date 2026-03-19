import os
from dotenv import load_dotenv
from openai import OpenAI

# Step 1: Load the API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Step 2: Create the OpenAI client
client = OpenAI(api_key=api_key)

# Step 3: Send a message
response = client.chat.completions.create(
    model="gpt-4o-mini",   # affordable and fast — perfect for this project
    max_tokens=256,
    messages=[
        {
            "role": "user",
            "content": "Say hello and tell me what you can help with in one sentence."
        }
    ]
)

# Step 4: Print the response
print("=== Raw response object ===")
print(response)

print("\n=== Just the text ===")
print(response.choices[0].message.content)

print("\n=== Useful metadata ===")
print(f"Model used   : {response.model}")
print(f"Input tokens : {response.usage.prompt_tokens}")
print(f"Output tokens: {response.usage.completion_tokens}")