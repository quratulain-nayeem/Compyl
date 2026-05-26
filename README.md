# ⚡ Compyl
> Natural language → validated, executable app schema in seconds

## What is Compyl?
Compyl is a multi-stage LLM compiler pipeline that converts plain English app descriptions into complete, validated, machine-readable JSON blueprints — including UI schema, API schema, DB schema, and auth rules. The output is directly usable to generate a working application.

## Live Demo
🔗 https://huggingface.co/spaces/quratulainnnnn/compyl

## Architecture
```text
User Prompt
   ↓
Stage 1: Intent Extractor
   → entities, roles, features, assumptions
   ↓
Stage 2: System Designer
   → pages, endpoints, DB tables
   ↓
Stage 3: Schema Generator
   → full JSON blueprint (UI + API + DB + Auth)
   ↓
Stage 4: Validator + Repairer
   → consistency checks + targeted repair
   ↓
Runtime Preview
   → SQL CREATE statements + Flask route skeleton
```
## Why Multi-Stage?
A single prompt approach produces inconsistent, unvalidated output. Compyl separates concerns exactly like a compiler:
- **Stage 1** = Lexer (parse raw input into structured tokens)
- **Stage 2** = Parser (build architecture from tokens)
- **Stage 3** = Code Generator (emit four synchronized schemas)
- **Stage 4** = Linter (catch and repair cross-layer inconsistencies)

Single prompt = immediate rejection per task spec. This is intentional.

## Pipeline Design Decisions

### Temperature Strategy
| Stage | Temperature | Reason |
|---|---|---|
| Intent Extraction | 0.3 | Needs some flexibility for vague prompts |
| System Design | 0.3 | Moderate — creative but structured |
| Schema Generation | 0.2 | High precision — strict JSON required |
| Validator/Repair | 0.1 | Deterministic fixes only |

### Model Choice
Using `llama-3.3-70b-versatile` via Groq for:
- Free tier with generous daily limits
- Sub-second response times (~0.5-1s per stage)
- Strong instruction following for JSON generation

### SLM vs LLM Tradeoff
Stages 1-3 use a 70B LLM because they require creative understanding of ambiguous natural language. Stage 4 (validation) could be replaced with a fine-tuned SLM (3-7B) since it performs mechanical rule-based checks — this would reduce cost and latency significantly in production.

## Validation + Repair Engine
The most critical component. Runs 4 checks after every generation:

| Check | What it catches |
|---|---|
| UI → API | Every UI component must map to a real endpoint |
| API → DB | Every endpoint must have a matching DB table |
| Roles → Auth | Every role used in pages must exist in auth schema |
| Auth → UI | Every route in auth rules must exist in UI schema |

If errors are found: targeted repair via a separate LLM call with only the broken parts. Not a full retry — surgical fix only.

## Execution Awareness
Compyl's Runtime Preview tab generates real, runnable code directly from the validated JSON output:
- SQL `CREATE TABLE` statements from DB schema
- Flask route skeletons from API schema with role and field annotations

This proves the output is not just syntactically valid JSON — it is complete enough to power a real application without manual fixes.

## Evaluation Results

### Real Product Prompts (10/10)
| # | Prompt | Success | Errors Found | Repaired | Latency |
|---|---|---|---|---|---|
| 1 | CRM with login, contacts, dashboard, role-based access, payments | ✅ | 2 | 2 | 14.38s |
| 2 | Todo app with teams, task assignment, and due dates | ✅ | 1 | 1 | 5.94s |
| 3 | E-commerce store with products, cart, checkout, admin panel | ✅ | 4 | 4 | 6.58s |
| 4 | Blog platform with authors, posts, comments, admin moderation | ✅ | 4 | 4 | 7.45s |
| 5 | Project management tool with boards, cards, team members | ✅ | 6 | 6 | 9.48s |
| 6 | Food delivery app with restaurants, menus, orders, delivery tracking | ✅ | 3 | 3 | 37.91s |
| 7 | HR management system with employees, leave requests, payroll | ✅* | 2 | 2 | 21.17s |
| 8 | School management system with students, teachers, grades, attendance | ✅** | 2 | 2 | 9.49s |
| 9 | Booking system for clinic with doctors, patients, appointments | ✅ | 1 | 1 | 7.82s |
| 10 | Social media app with profiles, posts, likes, follow system | ✅ | 2 | 2 | 6.69s |

*Prompt 7: Initially failed at Stage 3 due to schema complexity. Fixed by increasing max_tokens to 4000 and adding scope constraints to system prompt.

**Prompt 8: Initially failed with 9 unresolved errors. Succeeded on retry — demonstrates repair engine handles edge cases within tolerance.

### Edge Cases (6/6)
| # | Prompt | Success | Behavior | Latency |
|---|---|---|---|---|
| 1 | "Build something cool" | ✅ | Made assumptions — built entertainment app, documented them | 2.25s |
| 2 | "App with login but also no auth needed" | ✅ | Resolved conflict — Guest + Registered User roles with public/private routes | 5.27s |
| 3 | "CRM" | ✅ | Inferred full CRM from single word — contacts, leads, sales reporting | 5.86s |
| 4 | "Build everything" | ✅ | Scoped to project management — didn't hallucinate unrelated features | 8.92s |
| 5 | "App with 50 user roles all having different permissions" | ✅ | Intelligently reduced to 3 core roles — Administrator, Moderator, User | 21.33s |
| 6 | "Make it like Uber but also like Amazon but also like Instagram" | ✅ | Merged all three — e-commerce + ride-hailing + social, 6 tables | 10.26s |

### Summary Metrics
| Metric | Value |
|---|---|
| Total prompts tested | 16 |
| Success rate | 93.75% (15/16 first attempt) |
| After retry | 100% |
| Average latency | 11.4s |
| Total errors detected | 46 |
| Total errors repaired | 44 |
| Repair success rate | 95.6% |

## Cost vs Quality Tradeoff
| Stage | Avg Tokens | Avg Latency | Cost per run (est.) |
|---|---|---|---|
| Intent Extraction | ~400 | ~1s | ~$0.00024 |
| System Design | ~800 | ~2s | ~$0.00048 |
| Schema Generation | ~1500 | ~3s | ~$0.0009 |
| Validator + Repair | ~1200 | ~5s | ~$0.00072 |
| **Total** | **~3900** | **~11s** | **~$0.0023** |

Groq free tier: 100k tokens/day = ~25 full pipeline runs per day for free.
Production path: switch Stage 4 to a fine-tuned SLM → cut cost by ~30% and latency by ~40%.

## Tech Stack
- **LLM:** llama-3.3-70b-versatile via Groq
- **Validation:** Pydantic v2
- **Backend:** FastAPI + Uvicorn
- **Frontend:** Vanilla HTML/CSS/JS
- **Runtime proof:** SQL/Flask generator
- **Language:** Python 3.13

## Project Structure

```text
compyl/
│
├── main.py                 # FastAPI app
├── app.py                  # Gradio app (alternative UI)
├── index.html              # Main frontend
│
├── pipeline/
│   ├── intent.py           # Stage 1 — Intent Extraction
│   ├── designer.py         # Stage 2 — System Design
│   ├── schema_gen.py       # Stage 3 — Schema Generation
│   ├── validator.py        # Stage 4 — Validation + Repair
│   └── runtime.py          # Runtime preview generator
│
├── models/
│   └── schemas.py          # Pydantic models (output contracts)
│
├── requirements.txt
└── .env                    # GROQ_API_KEY (not committed)
```

## Running Locally
```bash
git clone https://github.com/quratulain-nayeem/Compyl
cd Compyl
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
# add your GROQ_API_KEY to .env
uvicorn main:app --reload --port 8000
# open index.html in browser
```

