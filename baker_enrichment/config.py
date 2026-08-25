"""Environment-only application configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import urlparse


DEFAULT_ENRICH_BASE_URL = "https://dev.enrich.so"


class ConfigurationError(ValueError):
    """Raised when required runtime configuration is absent or invalid."""


@dataclass(frozen=True, slots=True)
class EnrichSettings:
    api_key: str | None
    base_url: str = DEFAULT_ENRICH_BASE_URL
    # These deliberately stay below the Growth-plan ceilings of 300/min and 25/sec.
    requests_per_minute: int = 240
    requests_per_second_burst: int = 20

    def validate(self, *, require_api_key: bool) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ConfigurationError("ENRICH_BASE_URL must be an absolute HTTP(S) URL.")
        if require_api_key and not self.api_key:
            raise ConfigurationError(
                "ENRICH_API_KEY is required for a real run. Set it in the environment; "
                "do not place it in source code or spreadsheets."
            )


@dataclass(frozen=True, slots=True)
class LLMSettings:
    provider: str | None
    api_key: str | None
    model: str | None

    @property
    def enabled(self) -> bool:
        return bool(self.provider)

    def validate(self) -> None:
        if self.enabled and (not self.api_key or not self.model):
            raise ConfigurationError(
                "BAKER_LLM_PROVIDER requires both BAKER_LLM_API_KEY and BAKER_LLM_MODEL."
            )


@dataclass(frozen=True, slots=True)
class Settings:
    enrich: EnrichSettings
    llm: LLMSettings

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            enrich=EnrichSettings(
                api_key=_optional("ENRICH_API_KEY"),
                base_url=os.getenv("ENRICH_BASE_URL", DEFAULT_ENRICH_BASE_URL).rstrip("/"),
            ),
            llm=LLMSettings(
                provider=_optional("BAKER_LLM_PROVIDER"),
                api_key=_optional("BAKER_LLM_API_KEY"),
                model=_optional("BAKER_LLM_MODEL"),
            ),
        )

    def validate(self, *, require_enrich_api_key: bool) -> None:
        self.enrich.validate(require_api_key=require_enrich_api_key)
        self.llm.validate()


def _optional(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None
