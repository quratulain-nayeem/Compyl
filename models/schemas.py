from pydantic import BaseModel
from typing import List, Optional

# ─── STAGE 1 OUTPUT ───────────────────────────────────────
class IntentOutput(BaseModel):
    app_name: str
    app_type: str                    # e.g. "CRM", "E-commerce", "Todo App"
    features: List[str]              # e.g. ["login", "contacts", "dashboard"]
    user_roles: List[str]            # e.g. ["admin", "user"]
    entities: List[str]              # e.g. ["User", "Contact", "Payment"]
    has_payments: bool
    has_auth: bool
    assumptions: List[str]           # what your system assumed when prompt was vague

# ─── STAGE 2 OUTPUT ───────────────────────────────────────
class APIEndpoint(BaseModel):
    method: str                      # GET, POST, PUT, DELETE
    path: str                        # e.g. "/api/contacts"
    description: str
    required_fields: List[str]       # e.g. ["name", "email"]
    roles_allowed: List[str]         # e.g. ["admin", "user"]

class DBColumn(BaseModel):
    name: str
    type: str                        # e.g. "string", "integer", "boolean"
    required: bool

class DBTable(BaseModel):
    name: str
    columns: List[DBColumn]

class UIComponent(BaseModel):
    component_type: str              # e.g. "form", "table", "chart", "button"
    label: str
    maps_to_api: str                 # which endpoint this component calls

class UIPage(BaseModel):
    page_name: str
    route: str                       # e.g. "/dashboard"
    roles_allowed: List[str]
    components: List[UIComponent]

class SystemDesignOutput(BaseModel):
    pages: List[UIPage]
    endpoints: List[APIEndpoint]
    tables: List[DBTable]

# ─── STAGE 3 OUTPUT ───────────────────────────────────────
class AuthRule(BaseModel):
    role: str
    can_access: List[str]            # list of routes this role can access
    can_modify: List[str]            # list of routes this role can modify

class FullAppSchema(BaseModel):
    app_name: str
    app_type: str
    ui_schema: List[UIPage]
    api_schema: List[APIEndpoint]
    db_schema: List[DBTable]
    auth_schema: List[AuthRule]
    assumptions: List[str]

# ─── STAGE 4 OUTPUT ───────────────────────────────────────
class ValidationError(BaseModel):
    error_type: str                  # e.g. "missing_field", "schema_mismatch"
    location: str                    # e.g. "ui_schema.contacts_page"
    description: str
    repaired: bool

class FinalOutput(BaseModel):
    success: bool
    schema: FullAppSchema
    validation_errors: List[ValidationError]
    assumptions: List[str]
    retry_count: int