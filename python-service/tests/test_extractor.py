from pathlib import Path
from app.extractor import extract_fields, extract_text, ExtractionError


def test_ambiguous_amount_stays_null():
    text = Path("../../data/requests/request-03.txt").read_text(encoding="utf-8")
    extracted, evidence, amounts = extract_fields(text)
    assert amounts == [22000.0, 28000.0]
    assert extracted["amount"] is None
    assert extracted["currency"] is None
    assert extracted["reference"] == "CERT-303"


def test_pdf_is_extractable():
    pdf = Path("../../data/requests/request-02.pdf").read_bytes()
    text = extract_text("request-02.pdf", pdf)
    assert "HOME-202" in text
    assert "desk and chair" in text


def test_zero_byte_is_failure():
    try:
        extract_text("request-08.txt", b"")
    except ExtractionError as exc:
        assert str(exc) == "EMPTY_FILE"
    else:
        assert False, "expected EMPTY_FILE"
