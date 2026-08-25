"""Structured, privacy-conscious application logging."""

from __future__ import annotations

import json
import logging
from typing import Any


SENSITIVE_KEYS = frozenset({"api_key", "authorization", "email", "email_address", "phone", "cellphone"})


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        context = getattr(record, "context", {})
        payload.update(
            {key: _redact(value) if key.lower() in SENSITIVE_KEYS else value for key, value in context.items()}
        )
        return json.dumps(payload, default=str, sort_keys=True)


def configure_logging(*, verbose: bool = False) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)


def log_event(logger: logging.Logger, level: int, message: str, **context: Any) -> None:
    logger.log(level, message, extra={"context": context})


def _redact(value: Any) -> Any:
    return "[redacted]" if isinstance(value, str) else value
