import io
import re
from typing import Tuple
from pypdf import PdfReader


class ExtractionError(Exception):
    pass


def extract_text(filename: str, content: bytes) -> str:
    if not content:
        raise ExtractionError("EMPTY_FILE")
    lower = filename.lower()
    if lower.endswith(".txt"):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ExtractionError("INVALID_UTF8") from exc
        if not text.strip():
            raise ExtractionError("UNREADABLE_FILE")
        return text
    if lower.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(content))
            pages = [(p.extract_text() or "") for p in reader.pages]
            text = "\n".join(pages).strip()
        except Exception as exc:
            raise ExtractionError("PDF_EXTRACTION_FAILED") from exc
        if not text:
            raise ExtractionError("UNREADABLE_FILE")
        return text
    raise ExtractionError("UNSUPPORTED_FILE_TYPE")


def quote_for(text: str, pattern: str):
    m = re.search(pattern, text, flags=re.I)
    return m.group(0).strip() if m else None


def extract_fields(text: str):
    ref_match = re.search(r"Reference:\s*([A-Za-z0-9_-]+)", text, flags=re.I)
    references = ref_match.group(1) if ref_match else None

    amount_matches = re.findall(r"\b(?:INR|Rs\.?|₹)\s*([0-9][0-9,]*(?:\.\d+)?)", text, flags=re.I)
    numeric = [float(x.replace(",", "")) for x in amount_matches]

    # Also support "amount is 22000" only when no currency amount is present.
    if not numeric:
        generic = re.findall(r"\bamount\s+(?:is|of)\s+([0-9][0-9,]*(?:\.\d+)?)", text, flags=re.I)
        numeric = [float(x.replace(",", "")) for x in generic]

    amount = numeric[0] if len(set(numeric)) == 1 and numeric else None
    currency = "INR" if re.search(r"\bINR\b|₹|Rs\.?", text, re.I) else None

    if re.search(r"certification", text, re.I):
        benefit = "certification reimbursement"
    elif re.search(r"home[- ]office|desk and chair", text, re.I):
        benefit = "home-office allowance"
    elif re.search(r"external training|training", text, re.I):
        benefit = "external training"
    elif re.search(r"gym membership|wellness", text, re.I):
        benefit = "wellness benefit"
    elif re.search(r"rail travel|travel", text, re.I):
        benefit = "travel"
    else:
        benefit = None

    evidence_sentence = text.replace("\n", " ").strip()
    evidence = {
        "benefit": {"quote": evidence_sentence} if benefit else None,
        "amount": {"quote": evidence_sentence} if amount is not None else None,
        "currency": {"quote": evidence_sentence} if currency else None,
        "reference": {"quote": ref_match.group(0).strip()} if ref_match else None,
    }

    return {
        "benefit": benefit,
        "amount": amount,
        "currency": currency,
        "reference": references,
    }, evidence, numeric
