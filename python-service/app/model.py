import os
import time
from typing import List, Dict


class ModelProviderError(Exception):
    pass


class ModelProvider:
    def generate(self, question: str, eligible_policy_records: List[Dict]):
        raise NotImplementedError


class OfflineModelDouble(ModelProvider):
    def generate(self, question: str, eligible_policy_records: List[Dict]):
        mode = os.getenv("MODEL_MODE", "offline")
        if mode == "timeout":
            time.sleep(float(os.getenv("MODEL_TIMEOUT_MS", "1000")) / 1000 + 0.2)
            raise ModelProviderError("PROVIDER_TIMEOUT")
        if mode == "unavailable":
            raise ModelProviderError("PROVIDER_UNAVAILABLE")
        if mode == "malformed":
            return {"unexpected": "shape"}

        # Deterministic generation is intentionally simple. The policy service
        # already performed the hard eligibility filtering.
        if not eligible_policy_records:
            return {"status": "INSUFFICIENT_EVIDENCE", "answer": None, "citations": []}

        # Delegate final wording/decision to PolicyStore in the assessment baseline.
        return {"status": "READY", "eligible_count": len(eligible_policy_records)}
