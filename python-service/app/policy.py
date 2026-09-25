import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional


POLICY_PATH = Path(__file__).resolve().parents[2] / "data" / "policies" / "policies.json"

BENEFIT_PATTERNS = [
    ("certification", re.compile(r"certification|cloud certification", re.I)),
    ("home-office", re.compile(r"home[- ]office|desk and chair|home office", re.I)),
    ("travel", re.compile(r"rail travel|travel", re.I)),
    ("training", re.compile(r"external training|training", re.I)),
    ("wellness", re.compile(r"wellness|gym membership", re.I)),
]


class PolicyStore:
    def __init__(self, path: Path = POLICY_PATH):
        self.records = json.loads(path.read_text(encoding="utf-8"))

    def eligible(self, caller: Dict, as_of: date) -> List[Dict]:
        result = []
        for p in self.records:
            if p["approval_state"] != "Approved":
                continue
            if p["tenant"] != caller["tenant"] or p["role"] != caller["role"]:
                continue
            start = date.fromisoformat(p["effective_from"])
            end = date.fromisoformat(p["effective_to"])
            if start <= as_of < end:
                result.append(p)
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
        terms = {
            "certification": ("certification",),
            "home-office": ("home-office", "home office"),
            "travel": ("rail travel", "travel"),
            "training": ("training",),
            "wellness": ("wellness", "gym"),
        }[benefit]
        matches = []
        for p in eligible_records:
            hay = (p["text"] + " " + p["id"]).lower()
            if any(t in hay for t in terms):
                matches.append(p)
        return matches

    def answer(self, question: str, caller: Dict, as_of: date):
        eligible = self.eligible(caller, as_of)
        relevant = self.relevant(question, eligible)

        # Ignore the injection example as an answer source for unrelated benefits.
        # More importantly, the only records allowed to reach generation are already
        # tenant/role/date/approval eligible.
        if not relevant:
            return {"status": "INSUFFICIENT_EVIDENCE", "answer": None, "citations": []}

        normalized_quotes = [r["text"] for r in relevant]
        unique_quotes = list(dict.fromkeys(normalized_quotes))

        if len(unique_quotes) > 1:
            # Only treat simultaneous contradictory numeric allowance/limit records as conflict.
            numeric_values = []
            for q in unique_quotes:
                m = re.search(r"INR\s*([0-9]+)", q)
                numeric_values.append(m.group(1) if m else None)
            if len(set(v for v in numeric_values if v is not None)) > 1:
                return {
                    "status": "CONFLICT",
                    "answer": None,
                    "citations": [{"chunk_id": r["id"], "quote": r["text"]} for r in relevant],
                }

        r = relevant[0]
        benefit = self.infer_benefit(question)
        if benefit == "certification":
            answer = re.sub(r"^", "The applicable annual certification reimbursement limit is ", r["text"])
            # Use the source sentence as the evidence; produce a concise supported answer.
            m = re.search(r"(INR\s*[0-9]+)", r["text"])
            answer = f"The applicable annual certification reimbursement limit is {m.group(1)}."
        elif benefit == "home-office":
            m = re.search(r"(INR\s*[0-9]+)", r["text"])
            answer = f"The annual home-office allowance is {m.group(1)}."
        elif benefit == "travel":
            answer = r["text"]
        elif benefit == "training":
            answer = r["text"]
        else:
            return {"status": "INSUFFICIENT_EVIDENCE", "answer": None, "citations": []}

        return {
            "status": "ANSWERED",
            "answer": answer,
            "citations": [{"chunk_id": r["id"], "quote": r["text"]}],
        }
