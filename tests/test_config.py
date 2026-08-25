import pytest

from baker_enrichment.config import ConfigurationError, Settings


def test_real_run_requires_enrich_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENRICH_API_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="ENRICH_API_KEY"):
        Settings.from_environment().validate(require_enrich_api_key=True)


def test_dry_run_allows_missing_enrich_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENRICH_API_KEY", raising=False)
    Settings.from_environment().validate(require_enrich_api_key=False)


def test_llm_provider_requires_key_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BAKER_LLM_PROVIDER", "example")
    monkeypatch.delenv("BAKER_LLM_API_KEY", raising=False)
    monkeypatch.delenv("BAKER_LLM_MODEL", raising=False)
    with pytest.raises(ConfigurationError, match="BAKER_LLM_PROVIDER"):
        Settings.from_environment().validate(require_enrich_api_key=False)
