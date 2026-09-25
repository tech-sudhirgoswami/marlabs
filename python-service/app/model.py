import os
import time
from typing import Dict, List


class ModelProviderError(Exception):
    pass


class OfflineModelDouble:
    """Deterministic stand-in for the model provider.

    MODEL_MODE can be set to timeout, unavailable, or malformed to exercise
    the failure paths a real model would trigger.
    """

    def generate(self, question: str, eligible_policy_records: List[Dict]):
        mode = os.getenv("MODEL_MODE", "offline")
        if mode == "timeout":
            time.sleep(float(os.getenv("MODEL_TIMEOUT_MS", "1000")) / 1000)
            raise ModelProviderError("PROVIDER_TIMEOUT")
        if mode == "unavailable":
            raise ModelProviderError("PROVIDER_UNAVAILABLE")
        if mode == "malformed":
            return {"unexpected": "shape"}

        if not eligible_policy_records:
            return {"status": "INSUFFICIENT_EVIDENCE", "answer": None, "citations": []}
        return {"status": "READY", "eligible_count": len(eligible_policy_records)}
