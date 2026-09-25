import os
import pytest
from app.model import OfflineModelDouble, ModelProviderError


def test_unavailable_provider(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "unavailable")
    with pytest.raises(ModelProviderError):
        OfflineModelDouble().generate("q", [])


def test_timeout_provider(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "timeout")
    monkeypatch.setenv("MODEL_TIMEOUT_MS", "1")
    with pytest.raises(ModelProviderError):
        OfflineModelDouble().generate("q", [])


def test_malformed_output_is_controllable(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "malformed")
    result = OfflineModelDouble().generate("q", [])
    assert "unexpected" in result
