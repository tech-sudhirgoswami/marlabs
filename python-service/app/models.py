from typing import Optional, Dict, List, Any
from pydantic import BaseModel


class Caller(BaseModel):
    caller_id: str
    tenant: str
    role: str


class Citation(BaseModel):
    chunk_id: str
    quote: str


class PolicyResponse(BaseModel):
    status: str
    answer: Optional[str] = None
    citations: List[Citation] = []


class Extracted(BaseModel):
    benefit: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    reference: Optional[str] = None


class FieldEvidence(BaseModel):
    benefit: Optional[Dict[str, str]] = None
    amount: Optional[Dict[str, str]] = None
    currency: Optional[Dict[str, str]] = None
    reference: Optional[Dict[str, str]] = None


class BatchItem(BaseModel):
    document_id: str
    processing_status: str
    extracted: Optional[Extracted] = None
    field_evidence: Optional[FieldEvidence] = None
    policy: Optional[PolicyResponse] = None
    review_required: bool = True
    issues: List[str] = []
    duplicate_of: Optional[str] = None
    error: Optional[Dict[str, str]] = None
