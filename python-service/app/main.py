import base64
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .extractor import ExtractionError, extract_fields, extract_text
from .model import OfflineModelDouble
from .policy import PolicyStore


app = FastAPI(title="Marlabs Python Policy Service")
store = PolicyStore()
model = OfflineModelDouble()


class AnswerRequest(BaseModel):
    question: str
    as_of: str
    caller: dict


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

    caller = req.caller
    eligible = store.eligible(caller, as_of)
    result = model.generate(req.question, eligible)
    if result.get("status") not in ("READY", "INSUFFICIENT_EVIDENCE"):
        raise HTTPException(status_code=502, detail="MALFORMED_MODEL_OUTPUT")
    return store.answer(req.question, caller, as_of)


@app.post("/internal/process")
def process(req: DocumentRequest):
    try:
        content = base64.b64decode(req.content_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid content encoding")

    try:
        text = extract_text(req.filename, content)
        extracted, evidence, numeric_amounts = extract_fields(text)
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return {
        "text": text,
        "extracted": extracted,
        "field_evidence": evidence,
        "numeric_amounts": numeric_amounts,
    }
