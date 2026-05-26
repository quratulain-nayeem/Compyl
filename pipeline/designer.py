import os
import json
from groq import Groq
from dotenv import load_dotenv
from models.schemas import IntentOutput, SystemDesignOutput

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DESIGNER_SYSTEM_PROMPT = """
You are Stage 2 of Compyl — an AI app compiler.
You receive structured app intent and convert it into a system design.

You MUST respond with ONLY valid JSON. No explanation, no markdown, no backticks.
The JSON must exactly match this structure:

{
  "pages": [
    {
      "page_name": "string",
      "route": "string",
      "roles_allowed": ["string"],
      "components": [
        {
          "component_type": "string",
          "label": "string",
          "maps_to_api": "string"
        }
      ]
    }
  ],
  "endpoints": [
    {
      "method": "string",
      "path": "string",
      "description": "string",
      "required_fields": ["string"],
      "roles_allowed": ["string"]
    }
  ],
  "tables": [
    {
      "name": "string",
      "columns": [
        {
          "name": "string",
          "type": "string",
          "required": boolean
        }
      ]
    }
  ]
}

Rules:
- Every UI component must have a maps_to_api that matches an endpoint path
- Every endpoint must have a corresponding table in the DB
- Roles in pages and endpoints must match the roles from the intent
- method must be one of: GET, POST, PUT, DELETE
- component_type must be one of: form, table, chart, button, card, navbar
- column type must be one of: string, integer, boolean, timestamp, float, text
"""

def design_system(intent: IntentOutput) -> SystemDesignOutput:
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": DESIGNER_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Design the system for this app intent: {intent.model_dump_json()}"}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            raw = response.choices[0].message.content.strip()

            # strip markdown if model misbehaves
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            parsed = json.loads(raw)
            validated = SystemDesignOutput(**parsed)
            return validated

        except json.JSONDecodeError as e:
            retry_count += 1
            print(f"[Designer] JSON parse failed (attempt {retry_count}): {e}")

        except Exception as e:
            retry_count += 1
            print(f"[Designer] Validation failed (attempt {retry_count}): {e}")

    raise Exception(f"[Designer] Failed after {max_retries} attempts")


if __name__ == "__main__":
    # test using a fake intent output
    from pipeline.intent import extract_intent
    intent = extract_intent("Build a CRM with login, contacts, and dashboard")
    result = design_system(intent)
    print(result.model_dump_json(indent=2))