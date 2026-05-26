import gradio as gr
import json
import time
from pipeline.runtime import generate_runtime_preview
from pipeline.intent import extract_intent
from pipeline.designer import design_system
from pipeline.schema_gen import generate_schema
from pipeline.validator import validate_and_repair

def run_pipeline(user_prompt: str):
    if not user_prompt.strip():
        return "Please enter an app description.", "", "", ""

    logs = []
    start_time = time.time()

    try:
        # ── STAGE 1 ────────────────────────────────────────────
        logs.append("⚙️ Stage 1: Extracting intent...")
        t1 = time.time()
        intent = extract_intent(user_prompt)
        logs.append(f"✅ Intent extracted in {time.time() - t1:.2f}s")
        logs.append(f"   App type: {intent.app_type}")
        logs.append(f"   Features: {', '.join(intent.features)}")
        logs.append(f"   Roles: {', '.join(intent.user_roles)}")
        logs.append(f"   Entities: {', '.join(intent.entities)}")

        # ── STAGE 2 ────────────────────────────────────────────
        logs.append("\n⚙️ Stage 2: Designing system architecture...")
        t2 = time.time()
        design = design_system(intent)
        logs.append(f"✅ System designed in {time.time() - t2:.2f}s")
        logs.append(f"   Pages: {len(design.pages)}")
        logs.append(f"   Endpoints: {len(design.endpoints)}")
        logs.append(f"   DB Tables: {len(design.tables)}")

        # ── STAGE 3 ────────────────────────────────────────────
        logs.append("\n⚙️ Stage 3: Generating full schema...")
        t3 = time.time()
        schema = generate_schema(intent, design)
        logs.append(f"✅ Schema generated in {time.time() - t3:.2f}s")

        # ── STAGE 4 ────────────────────────────────────────────
        logs.append("\n⚙️ Stage 4: Validating and repairing...")
        t4 = time.time()
        result = validate_and_repair(schema)
        logs.append(f"✅ Validation complete in {time.time() - t4:.2f}s")
        if result.validation_errors:
            logs.append(f"   ⚠️ {len(result.validation_errors)} issue(s) found and repaired:")
            for e in result.validation_errors:
                status = "✅ repaired" if e.repaired else "❌ unresolved"
                logs.append(f"      [{e.error_type}] {e.location} → {status}")
        else:
            logs.append("   ✅ No issues found")

        total_time = time.time() - start_time
        logs.append(f"\n🏁 Pipeline complete in {total_time:.2f}s")
        logs.append(f"   Success: {result.success}")
        logs.append(f"   Retry count: {result.retry_count}")
        runtime_output = generate_runtime_preview(result.schema)
        # ── FORMAT OUTPUTS ─────────────────────────────────────
        pipeline_log = "\n".join(logs)

        full_schema = json.loads(result.schema.model_dump_json(indent=2))

        ui_output = json.dumps(full_schema.get("ui_schema", {}), indent=2)
        api_output = json.dumps(full_schema.get("api_schema", {}), indent=2)
        db_output = json.dumps({
            "db_schema": full_schema.get("db_schema", {}),
            "auth_schema": full_schema.get("auth_schema", {})
        }, indent=2)

        return pipeline_log, ui_output, api_output, db_output, runtime_output

    except Exception as e:
        error_msg = f"❌ Pipeline failed: {str(e)}"
        logs.append(error_msg)
        return "\n".join(logs), "", "", "", ""

# ── GRADIO UI ──────────────────────────────────────────────────────────
with gr.Blocks(
    title="Compyl",
    theme=gr.themes.Soft(),
    css="""
        .header { text-align: center; padding: 20px; }
        .header h1 { font-size: 2.5em; font-weight: 800; color: #6366f1; }
        .header p { color: #6b7280; font-size: 1.1em; }
        .stage-box { border-left: 3px solid #6366f1; padding-left: 10px; }
    """
) as demo:

    gr.HTML("""
        <div class="header">
            <h1>⚡ Compyl</h1>
            <p>Natural language → validated app schema in seconds</p>
            <p style="font-size:0.9em; color:#9ca3af;">
                Multi-stage LLM pipeline: Intent → Design → Schema → Validation
            </p>
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            prompt_input = gr.Textbox(
                label="Describe your app",
                placeholder='e.g. "Build a CRM with login, contacts, dashboard, role-based access, and payments. Admins can see analytics."',
                lines=4
            )
            run_btn = gr.Button("⚡ Generate Schema", variant="primary", size="lg")

            gr.Examples(
                examples=[
                    ["Build a CRM with login, contacts, dashboard, role-based access, and payments. Admins can see analytics."],
                    ["Todo app with teams, task assignment, and due dates"],
                    ["E-commerce store with products, cart, checkout, and admin panel"],
                    ["Blog platform with authors, posts, comments, and admin moderation"],
                    ["Build something cool"],
                ],
                inputs=prompt_input,
                label="Try these examples"
            )

        with gr.Column(scale=2):
            pipeline_log = gr.Textbox(
                label="⚙️ Pipeline Log",
                lines=12,
                interactive=False
            )

    # ── TABS OUTSIDE THE ROW ──────────────────────────────────────────
    with gr.Tabs():
        with gr.Tab("🖥️ UI Schema"):
            ui_output = gr.Code(
                language="json",
                label="UI Schema",
                wrap_lines=False,
                max_lines=30
            )
        with gr.Tab("🔌 API Schema"):
            api_output = gr.Code(
                language="json",
                label="API Schema",
                wrap_lines=False,
                max_lines=30
            )
        
        with gr.Tab("🗄️ DB + Auth Schema"):
            db_output = gr.Code(
                language="json",
                label="DB + Auth Schema",
                wrap_lines=False,
                max_lines=30
            )
        with gr.Tab("🚀 Runtime Preview"):
         runtime_output = gr.Code(
            language="python",
            label="Runtime Preview (SQL + Flask)",
            wrap_lines=False,
            max_lines=30
    )
    run_btn.click(
    fn=run_pipeline,
    inputs=prompt_input,
    outputs=[pipeline_log, ui_output, api_output, db_output, runtime_output]
)
if __name__ == "__main__":
    demo.launch()