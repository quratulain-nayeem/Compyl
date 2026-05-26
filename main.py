from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pipeline.intent import extract_intent
from pipeline.designer import design_system
from pipeline.schema_gen import generate_schema
from pipeline.validator import validate_and_repair
from pipeline.runtime import generate_runtime_preview
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
async def home():
    return FileResponse("index.html")

@app.post("/generate")
async def generate(req: PromptRequest):
    try:
        intent = extract_intent(req.prompt)
        design = design_system(intent)
        schema = generate_schema(intent, design)
        result = validate_and_repair(schema)
        runtime = generate_runtime_preview(result.schema)

        full_schema = json.loads(result.schema.model_dump_json())

        return {
            "success": result.success,
            "intent": intent.model_dump(),
            "ui_schema": full_schema.get("ui_schema"),
            "api_schema": full_schema.get("api_schema"),
            "db_schema": full_schema.get("db_schema"),
            "auth_schema": full_schema.get("auth_schema"),
            "assumptions": result.assumptions,
            "validation_errors": [e.model_dump() for e in result.validation_errors],
            "retry_count": result.retry_count,
            "runtime_preview": runtime
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
