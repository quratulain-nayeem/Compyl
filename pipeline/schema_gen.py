import os
import json
from groq import Groq
from dotenv import load_dotenv
from models.schemas import IntentOutput, SystemDesignOutput, FullAppSchema

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SCHEMA_GEN_SYSTEM_PROMPT = """
You are Stage 3 of Compyl — an AI app compiler.
You receive app intent and system design, and produce the final complete app schema.

You MUST respond with ONLY valid JSON. No explanation, no markdown, no backticks.
The JSON must exactly match this structure:

{
  "app_name": "string",
  "app_type": "string",
  "ui_schema": [ ...same as pages format... ],
  "api_schema": [ ...same as endpoints format... ],
  "db_schema": [ ...same as tables format... ],
  "auth_schema": [
    {
      "role": "string",
      "can_access": ["string"],
      "can_modify": ["string"]
    }
  ],
  "assumptions": ["string"]
}

Rules:
- ui_schema must use EXACTLY the same pages from the system design
- api_schema must use EXACTLY the same endpoints from the system design
- db_schema must use EXACTLY the same tables from the system design
- auth_schema must define rules for EVERY role in the intent
- can_access is a list of routes the role can view
- can_modify is a list of routes the role can make POST/PUT/DELETE calls to
- assumptions must carry over from intent plus any new ones you make
- Do NOT invent new pages, endpoints, or tables not in the system design
- If the schema would be very large, limit to maximum 4 pages, 6 endpoints, and 4 tables. Prioritize core features only.
"""

def generate_schema(intent: IntentOutput, design: SystemDesignOutput) -> FullAppSchema:
    max_retries = 3
    retry_count = 0

    combined_input = {
        "intent": intent.model_dump(),
        "design": design.model_dump()
    }

    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SCHEMA_GEN_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Generate the full app schema from this intent and design: {json.dumps(combined_input)}"}
                ],
                temperature=0.2,
                max_tokens=4000
            )

            raw = response.choices[0].message.content.strip()

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            parsed = json.loads(raw)
            validated = FullAppSchema(**parsed)
            return validated

        except json.JSONDecodeError as e:
            retry_count += 1
            print(f"[SchemaGen] JSON parse failed (attempt {retry_count}): {e}")

        except Exception as e:
            retry_count += 1
            print(f"[SchemaGen] Validation failed (attempt {retry_count}): {e}")

    raise Exception(f"[SchemaGen] Failed after {max_retries} attempts")


if __name__ == "__main__":
    from pipeline.intent import extract_intent
    from pipeline.designer import design_system

    intent = extract_intent("Build a CRM with login, contacts, and dashboard")
    design = design_system(intent)
    result = generate_schema(intent, design)
    print(result.model_dump_json(indent=2))