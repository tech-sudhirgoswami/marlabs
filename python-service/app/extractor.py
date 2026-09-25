import io
import re

from pypdf import PdfReader


class ExtractionError(Exception):
    pass


def extract_text(filename: str, content: bytes) -> str:
    if not content:
        raise ExtractionError("EMPTY_FILE")
    if filename.lower().endswith(".txt"):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ExtractionError("INVALID_UTF8") from exc
        if not text.strip():
            raise ExtractionError("UNREADABLE_FILE")
        return text
    if filename.lower().endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception as exc:
            raise ExtractionError("PDF_EXTRACTION_FAILED") from exc
        if not text:
            raise ExtractionError("UNREADABLE_FILE")
        return text
    raise ExtractionError("UNSUPPORTED_FILE_TYPE")


def extract_fields(text: str):
    reference_match = re.search(r"Reference:\s*([A-Za-z0-9_-]+)", text, flags=re.I)
    reference = reference_match.group(1) if reference_match else None

    amounts = re.findall(r"\b(?:INR|Rs\.?|₹)\s*([0-9][0-9,]*(?:\.\d+)?)", text, flags=re.I)
    numeric = [float(value.replace(",", "")) for value in amounts]

    # Without a currency prefix, accept "amount is <value>" as a fallback.
    if not numeric:
        generic = re.findall(r"\bamount\s+(?:is|of)\s+([0-9][0-9,]*(?:\.\d+)?)", text, flags=re.I)
        numeric = [float(value.replace(",", "")) for value in generic]

    amount = numeric[0] if numeric and len(set(numeric)) == 1 else None
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

    quote = text.replace("\n", " ").strip()
    evidence = {
        "benefit": {"quote": quote} if benefit else None,
        "amount": {"quote": quote} if amount is not None else None,
        "currency": {"quote": quote} if currency else None,
        "reference": {"quote": reference_match.group(0).strip()} if reference_match else None,
    }

    return {
        "benefit": benefit,
        "amount": amount,
        "currency": currency,
        "reference": reference,
    }, evidence, numeric
