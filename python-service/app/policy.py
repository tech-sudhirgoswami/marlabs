import json
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional


POLICY_PATH = Path(__file__).resolve().parents[2] / "data" / "policies" / "policies.json"

BENEFIT_PATTERNS = [
    ("certification", re.compile(r"certification", re.I)),
    ("home-office", re.compile(r"home[- ]office|desk and chair", re.I)),
    ("travel", re.compile(r"rail travel|travel", re.I)),
    ("training", re.compile(r"external training|training", re.I)),
    ("wellness", re.compile(r"wellness|gym membership", re.I)),
]

TERMS = {
    "certification": ("certification",),
    "home-office": ("home-office", "home office"),
    "travel": ("rail travel", "travel"),
    "training": ("training",),
    "wellness": ("wellness", "gym"),
}


class PolicyStore:
    def __init__(self, path: Path = POLICY_PATH):
        self.records = json.loads(path.read_text(encoding="utf-8"))

    def eligible(self, caller: Dict, as_of: date) -> List[Dict]:
        result = []
        for record in self.records:
            if record["approval_state"] != "Approved":
                continue
            if record["tenant"] != caller["tenant"] or record["role"] != caller["role"]:
                continue
            start = date.fromisoformat(record["effective_from"])
            end = date.fromisoformat(record["effective_to"])
            if start <= as_of < end:
                result.append(record)
        return result

    def infer_benefit(self, text: str) -> Optional[str]:
        for benefit, pattern in BENEFIT_PATTERNS:
            if pattern.search(text):
                return benefit
        return None

    def relevant(self, text: str, eligible_records: List[Dict]) -> List[Dict]:
        benefit = self.infer_benefit(text)
        if not benefit:
            return []
        return [
            record
            for record in eligible_records
            if any(term in f"{record['text']} {record['id']}".lower() for term in TERMS[benefit])
        ]

    def answer(self, question: str, caller: Dict, as_of: date):
        relevant = self.relevant(question, self.eligible(caller, as_of))
        if not relevant:
            return {"status": "INSUFFICIENT_EVIDENCE", "answer": None, "citations": []}

        # Contradictory applicable limits are reported as a conflict; no
        # precedence rule is supplied, so one is not invented.
        quotes = list(dict.fromkeys(record["text"] for record in relevant))
        amounts = set()
        for quote in quotes:
            match = re.search(r"INR\s*([0-9]+)", quote)
            if match:
                amounts.add(match.group(1))
        if len(amounts) > 1:
            return {
                "status": "CONFLICT",
                "answer": None,
                "citations": [{"chunk_id": r["id"], "quote": r["text"]} for r in relevant],
            }

        record = relevant[0]
        benefit = self.infer_benefit(question)
        if benefit == "certification":
            amount = re.search(r"INR\s*[0-9]+", record["text"]).group(0)
            result = f"The applicable annual certification reimbursement limit is {amount}."
        elif benefit == "home-office":
            amount = re.search(r"INR\s*[0-9]+", record["text"]).group(0)
            result = f"The annual home-office allowance is {amount}."
        elif benefit in ("travel", "training"):
            result = record["text"]
        else:
            return {"status": "INSUFFICIENT_EVIDENCE", "answer": None, "citations": []}

        return {
            "status": "ANSWERED",
            "answer": result,
            "citations": [{"chunk_id": record["id"], "quote": record["text"]}],
        }
