# ⚡ Compyl
> Natural language → validated, executable app schema in seconds

## What is Compyl?
Compyl is a multi-stage LLM compiler pipeline that converts plain English app descriptions into complete, validated, machine-readable JSON blueprints — including UI schema, API schema, DB schema, and auth rules.

## Architecture
User Prompt
↓
Stage 1: Intent Extractor     → entities, roles, features
↓
Stage 2: System Designer      → pages, endpoints, tables
↓
Stage 3: Schema Generator     → full JSON blueprint
↓
Stage 4: Validator + Repairer → consistency checks + targeted repair
↓
Runtime Preview               → SQL + Flask skeleton

## Pipeline Design
Each stage is a separate LLM call with its own system prompt, output schema, and retry logic. This is intentional — it mirrors how a compiler separates lexing, parsing, and code generation into distinct phases.

- **Temperature:** 0.3 → 0.2 across stages (decreasing creativity, increasing precision)
- **Model:** llama-3.3-70b-versatile via Groq (chosen for speed + free tier)
- **Validation:** Pydantic models enforce strict output contracts at every stage
- **Repair:** Targeted re-generation of broken parts only — not full retry

## Validation Checks
| Check | Description |
|---|---|
| UI → API | Every UI component must map to a real endpoint |
| API → DB | Every endpoint must have a matching DB table |
| Roles → Auth | Every role used in pages must exist in auth schema |
| Auth → UI | Every route in auth rules must exist in UI schema |

## Evaluation Results

### Real Product Prompts
| # | Prompt | Success | Errors Found | Repaired | Latency |
|---|---|---|---|---|---|
| 1 | CRM with login, contacts, dashboard | ✅ | 2 | 2 | 14.38s |
| 2 | | | | | |
...

### Edge Cases
| # | Prompt | Success | Behavior | Latency |
|---|---|---|---|---|
| 1 | "Build something cool" | ✅ | Made assumptions, documented them | Xs |
...

## Cost vs Quality Tradeoff
| Stage | Avg Tokens | Avg Latency | Purpose |
|---|---|---|---|
| Intent | ~400 | ~2s | High creativity needed |
| Designer | ~800 | ~3s | Moderate complexity |
| Schema Gen | ~1500 | ~4s | High precision needed |
| Validator | ~1200 | ~10s | Repair if needed |
| **Total** | **~3900** | **~19s** | |

## Tech Stack
- Python + Groq (llama-3.3-70b-versatile)
- Pydantic for schema validation
- Gradio for UI
- HuggingFace Spaces for hosting
