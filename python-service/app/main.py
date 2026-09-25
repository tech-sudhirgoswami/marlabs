from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from .policy import PolicyStore
from .extractor import extract_text, extract_fields, ExtractionError
from .model import OfflineModelDouble, ModelProviderError


app = FastAPI(title="Marlabs Python Policy Service")
store = PolicyStore()
model = OfflineModelDouble()


class CallerRequest(BaseModel):
    caller_id: str
    tenant: str
    role: str


class AnswerRequest(BaseModel):
    question: str
    as_of: str
    caller: CallerRequest


class DocumentRequest(BaseModel):
    filename: str
    content_b64: str


@app.get("/health")
def health():
    return {"status": "UP"}


@app.post("/internal/answer")
def answer(req: AnswerRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question must be non-empty")
    try:
        as_of = date.fromisoformat(req.as_of)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid as_of")
    caller = req.caller.model_dump()
    eligible = store.eligible(caller, as_of)
    # Provider sees only eligible records.
    provider_result = model.generate(req.question, eligible)
    if provider_result.get("status") != "READY" and provider_result.get("status") != "INSUFFICIENT_EVIDENCE":
        raise HTTPException(status_code=502, detail="MALFORMED_MODEL_OUTPUT")
    return store.answer(req.question, caller, as_of)


@app.post("/internal/process")
def process(req: DocumentRequest):
    import base64
    try:
        content = base64.b64decode(req.content_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid content encoding")

    try:
        text = extract_text(req.filename, content)
        extracted, evidence, numeric_amounts = extract_fields(text)
        return {
            "text": text,
            "extracted": extracted,
            "field_evidence": evidence,
            "numeric_amounts": numeric_amounts,
        }
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
