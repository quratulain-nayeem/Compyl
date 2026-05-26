from models.schemas import FullAppSchema

def generate_runtime_preview(schema: FullAppSchema) -> str:
    output = []

    # ── SQL FROM DB SCHEMA ─────────────────────────────────────
    output.append("-- ============================================")
    output.append(f"-- {schema.app_name} — Generated SQL Schema")
    output.append("-- ============================================\n")

    type_map = {
        "string": "VARCHAR(255)",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "timestamp": "TIMESTAMP",
        "float": "FLOAT",
        "text": "TEXT"
    }

    for table in schema.db_schema:
        output.append(f"CREATE TABLE {table.name} (")
        col_lines = []
        for col in table.columns:
            sql_type = type_map.get(col.type, "VARCHAR(255)")
            not_null = "NOT NULL" if col.required else ""
            if col.name == "id":
                col_lines.append(f"  {col.name} {sql_type} PRIMARY KEY")
            else:
                col_lines.append(f"  {col.name} {sql_type} {not_null}".strip())
        output.append(",\n".join(col_lines))
        output.append(");\n")

    # ── FLASK ROUTES FROM API SCHEMA ───────────────────────────
    output.append("\n# ============================================")
    output.append(f"# {schema.app_name} — Generated Flask Routes")
    output.append("# ============================================\n")
    output.append("from flask import Flask, request, jsonify")
    output.append("app = Flask(__name__)\n")

    for endpoint in schema.api_schema:
        method = endpoint.method
        path = endpoint.path
        roles = ", ".join(endpoint.roles_allowed) if endpoint.roles_allowed else "public"
        fields = ", ".join(endpoint.required_fields) if endpoint.required_fields else "none"

        func_name = path.replace("/", "_").replace("-", "_").strip("_")

        output.append(f"@app.route('{path}', methods=['{method}'])")
        output.append(f"def {func_name}():")
        output.append(f"    # roles_allowed: {roles}")
        if endpoint.required_fields:
            output.append(f"    # required_fields: {fields}")
        output.append(f"    # {endpoint.description}")
        output.append(f"    pass\n")

    # ── AUTH RULES SUMMARY ─────────────────────────────────────
    output.append("\n# ============================================")
    output.append("# Auth Rules Summary")
    output.append("# ============================================\n")

    for rule in schema.auth_schema:
        output.append(f"# Role: {rule.role}")
        output.append(f"#   Can access: {', '.join(rule.can_access)}")
        output.append(f"#   Can modify: {', '.join(rule.can_modify)}\n")

    return "\n".join(output)