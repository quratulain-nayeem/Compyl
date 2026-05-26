import os
import json
from groq import Groq
from dotenv import load_dotenv
from models.schemas import FullAppSchema, FinalOutput, ValidationError

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def validate_and_repair(schema: FullAppSchema, retry_count: int = 0) -> FinalOutput:
    errors = []

    # ── CHECK 1: UI components must map to real API paths ──────────────
    api_paths = [e.path for e in schema.api_schema]
    for page in schema.ui_schema:
        for component in page.components:
            if component.maps_to_api not in api_paths:
                errors.append(ValidationError(
                    error_type="ui_api_mismatch",
                    location=f"ui_schema.{page.page_name}.{component.label}",
                    description=f"Component maps to '{component.maps_to_api}' but this endpoint doesn't exist in api_schema",
                    repaired=False
                ))

    # ── CHECK 2: API endpoints must have matching DB table ─────────────
    table_names = [t.name.lower() for t in schema.db_schema]
    for endpoint in schema.api_schema:
        # extract resource name from path e.g. /api/contacts → contacts
        parts = [p for p in endpoint.path.split("/") if p and p != "api"]
        if parts:
            resource = parts[0].lower()
            # check if any table name contains the resource name
            matched = any(resource in t for t in table_names)
            if not matched:
                errors.append(ValidationError(
                    error_type="api_db_mismatch",
                    location=f"api_schema.{endpoint.path}",
                    description=f"Endpoint '{endpoint.path}' has no matching table in db_schema (looking for '{resource}')",
                    repaired=False
                ))

    # ── CHECK 3: Roles in pages must exist in auth schema ──────────────
    auth_roles = [a.role.lower() for a in schema.auth_schema]
    for page in schema.ui_schema:
        for role in page.roles_allowed:
            if role.lower() not in auth_roles:
                errors.append(ValidationError(
                    error_type="undefined_role",
                    location=f"ui_schema.{page.page_name}",
                    description=f"Role '{role}' is used in page but not defined in auth_schema",
                    repaired=False
                ))

    # ── CHECK 4: Auth routes must exist in UI schema ───────────────────
    ui_routes = [p.route for p in schema.ui_schema]
    for auth_rule in schema.auth_schema:
        for route in auth_rule.can_access:
            if route not in ui_routes:
                errors.append(ValidationError(
                    error_type="auth_route_missing",
                    location=f"auth_schema.{auth_rule.role}",
                    description=f"Auth rule references route '{route}' but it doesn't exist in ui_schema",
                    repaired=False
                ))

    # ── REPAIR: if errors found, ask LLM to fix specific parts ─────────
    if errors:
        error_descriptions = [e.description for e in errors]
        repaired_schema = attempt_repair(schema, error_descriptions)

        if repaired_schema:
            # mark errors as repaired
            for e in errors:
                e.repaired = True
            schema = repaired_schema

    return FinalOutput(
        success=len([e for e in errors if not e.repaired]) == 0,
        schema=schema,
        validation_errors=errors,
        assumptions=schema.assumptions,
        retry_count=retry_count
    )


def attempt_repair(schema: FullAppSchema, errors: list) -> FullAppSchema:
    """
    Targeted repair — only fixes the broken parts, not a full regeneration.
    """
    repair_prompt = f"""
You are the repair engine of Compyl.
The following schema has these specific errors:

ERRORS:
{json.dumps(errors, indent=2)}

CURRENT SCHEMA:
{schema.model_dump_json(indent=2)}

Fix ONLY the errors listed above. 
Do not change anything else.
Return the complete corrected schema as valid JSON only.
No markdown, no backticks, no explanation.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": repair_prompt}
            ],
            temperature=0.1,  # very low — we want precise fixes only
            max_tokens=3000
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw)
        return FullAppSchema(**parsed)

    except Exception as e:
        print(f"[Validator] Repair failed: {e}")
        return None


if __name__ == "__main__":
    from pipeline.intent import extract_intent
    from pipeline.designer import design_system
    from pipeline.schema_gen import generate_schema

    intent = extract_intent("Build a CRM with login, contacts, and dashboard")
    design = design_system(intent)
    schema = generate_schema(intent, design)
    result = validate_and_repair(schema)

    print("\n=== VALIDATION RESULT ===")
    print(f"Success: {result.success}")
    print(f"Errors found: {len(result.validation_errors)}")
    for e in result.validation_errors:
        print(f"  [{e.error_type}] {e.location}: {e.description} | Repaired: {e.repaired}")
    print(f"\nFinal schema valid: {result.success}")