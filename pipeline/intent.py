import os
import json
from groq import Groq
from dotenv import load_dotenv
from models.schemas import IntentOutput

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

INTENT_SYSTEM_PROMPT = """
You are Stage 1 of Compyl — an AI app compiler.
Your job is to extract structured intent from a user's app description.

You MUST respond with ONLY valid JSON. No explanation, no markdown, no backticks.
The JSON must exactly match this structure:

{
  "app_name": "string",
  "app_type": "string",
  "features": ["string"],
  "user_roles": ["string"],
  "entities": ["string"],
  "has_payments": boolean,
  "has_auth": boolean,
  "assumptions": ["string"]
}

Rules:
- If the prompt is vague, make reasonable assumptions and list them in "assumptions"
- Always include at least one role in user_roles
- entities are the main data objects (e.g. User, Product, Order)
- Keep features as simple action-based strings (e.g. "user login", "view dashboard")
- If prompt is completely unusable, still return valid JSON with assumptions explaining what you guessed
"""

def extract_intent(user_prompt: str) -> IntentOutput:
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extract intent from this app description: {user_prompt}"}
                ],
                temperature=0.3,   # low temp = more consistent output
                max_tokens=1000
            )

            raw = response.choices[0].message.content.strip()

            # strip markdown if model misbehaves
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            
            parsed = json.loads(raw)
            validated = IntentOutput(**parsed)
            return validated

        except json.JSONDecodeError as e:
            retry_count += 1
            print(f"[Intent] JSON parse failed (attempt {retry_count}): {e}")

        except Exception as e:
            retry_count += 1
    raise ValueError("Failed to extract intent after multiple retries")

if __name__ == "__main__":
    result = extract_intent("Build a CRM with login, contacts, and dashboard")
    print(result.model_dump_json(indent=2))