from datetime import date
from pathlib import Path
from app.policy import PolicyStore


CALLER = {"caller_id": "atlas-employee-01", "tenant": "Atlas", "role": "employee"}


def test_current_certification_limit():
    store = PolicyStore()
    result = store.answer("What is my annual certification reimbursement limit?", CALLER, date(2026,9,21))
    assert result["status"] == "ANSWERED"
    assert "INR 25000" in result["answer"]
    assert result["citations"][0]["chunk_id"] == "atlas-cert-current"
    assert result["citations"][0]["quote"] == "The annual certification reimbursement limit for employees is INR 25000."


def test_historical_and_future_effective_dates():
    store = PolicyStore()
    historical = store.answer("What is my annual certification reimbursement limit?", CALLER, date(2026,5,31))
    future = store.answer("What is my annual certification reimbursement limit?", CALLER, date(2027,1,1))
    assert "INR 40000" in historical["answer"]
    assert "INR 35000" in future["answer"]


def test_home_office_conflict_is_not_resolved_by_invention():
    store = PolicyStore()
    result = store.answer("What is my home-office allowance?", CALLER, date(2026,9,21))
    assert result["status"] == "CONFLICT"
    assert {c["chunk_id"] for c in result["citations"]} == {"atlas-home-office-a", "atlas-home-office-b"}


def test_tenant_and_role_are_enforced():
    store = PolicyStore()
    boreal = {"caller_id":"boreal-employee-01","tenant":"Boreal","role":"employee"}
    atlas_contractor = {"caller_id":"atlas-contractor-01","tenant":"Atlas","role":"contractor"}
    r1 = store.answer("What is my certification reimbursement limit?", boreal, date(2026,9,21))
    r2 = store.answer("What is my certification reimbursement limit?", atlas_contractor, date(2026,9,21))
    assert "INR 80000" in r1["answer"]
    assert "INR 10000" in r2["answer"]


def test_draft_is_not_eligible():
    store = PolicyStore()
    result = store.answer("What is my certification reimbursement limit?", CALLER, date(2026,9,21))
    assert all(c["chunk_id"] != "atlas-cert-draft" for c in result["citations"])


def test_unknown_wellness_policy_is_insufficient():
    store = PolicyStore()
    result = store.answer("What wellness benefit am I entitled to?", CALLER, date(2026,9,21))
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["citations"] == []
