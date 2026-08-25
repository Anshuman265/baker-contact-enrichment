"""Small synchronous HTTP client with retry and Enrich-aware error handling."""

from __future__ import annotations

from dataclasses import dataclass
import json
import socket
import time
from collections.abc import Callable
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from baker_enrichment.config import EnrichSettings
from baker_enrichment.rate_limiter import SlidingWindowRateLimiter


RETRYABLE_STATUS_CODES = frozenset({429})


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes


class HttpTransport(Protocol):
    def send(self, request: Request, timeout: float) -> HttpResponse: ...


class UrlLibTransport:
    def send(self, request: Request, timeout: float) -> HttpResponse:
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310 -- URL comes from validated settings.
                return HttpResponse(response.status, dict(response.headers.items()), response.read())
        except HTTPError as error:
            return HttpResponse(error.code, dict(error.headers.items()) if error.headers else {}, error.read())


@dataclass(frozen=True, slots=True)
class ApiError(RuntimeError):
    endpoint: str
    message: str
    status_code: int | None
    request_context: dict[str, str]
    retry_count: int
    request_id: str | None = None

    def __str__(self) -> str:
        status = str(self.status_code) if self.status_code is not None else "network"
        return f"Enrich API {status} error at {self.endpoint}: {self.message}"


class EnrichApiClient:
    """Transport-level client shared by endpoint-specific API clients."""

    def __init__(
        self,
        settings: EnrichSettings,
        *,
        transport: HttpTransport | None = None,
        rate_limiter: SlidingWindowRateLimiter | None = None,
        timeout_seconds: float = 20.0,
        max_retries: int = 3,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        settings.validate(require_api_key=True)
        self._settings = settings
        self._transport = transport or UrlLibTransport()
        self._rate_limiter = rate_limiter or SlidingWindowRateLimiter(
            burst_limit=settings.requests_per_second_burst,
            sustained_limit=settings.requests_per_minute,
        )
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._sleeper = sleeper

    def post_json(self, endpoint: str, payload: dict[str, Any], *, context: dict[str, str]) -> dict[str, Any]:
        return self._request_json("POST", endpoint, payload, context=context)

    def get_json(self, endpoint: str, *, context: dict[str, str]) -> dict[str, Any]:
        return self._request_json("GET", endpoint, None, context=context)

    def _request_json(
        self, method: str, endpoint: str, payload: dict[str, Any] | None, *, context: dict[str, str]
    ) -> dict[str, Any]:
        url = f"{self._settings.base_url}{endpoint}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        for retry_count in range(self._max_retries + 1):
            self._rate_limiter.acquire()
            request = Request(
                url,
                data=body,
                method=method,
                headers={"x-api-key": self._settings.api_key or "", "Content-Type": "application/json"},
            )
            try:
                response = self._transport.send(request, self._timeout_seconds)
            except (TimeoutError, socket.timeout, URLError, ConnectionError, OSError) as error:
                if retry_count < self._max_retries:
                    self._sleeper(self._backoff_seconds(retry_count))
                    continue
                raise ApiError(endpoint, str(error), None, context, retry_count) from error

            request_id = _request_id(response.headers)
            if 200 <= response.status_code < 300:
                try:
                    decoded = json.loads(response.body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise ApiError(endpoint, "Response was not valid JSON.", response.status_code, context, retry_count, request_id) from error
                if not isinstance(decoded, dict):
                    raise ApiError(endpoint, "Response JSON must be an object.", response.status_code, context, retry_count, request_id)
                if decoded.get("success") is False:
                    raise ApiError(
                        endpoint,
                        "Enrich response reported success=false.",
                        response.status_code,
                        context,
                        retry_count,
                        request_id,
                    )
                return decoded

            message = _error_message(response.body)
            retryable = response.status_code in RETRYABLE_STATUS_CODES or response.status_code >= 500
            if retryable and retry_count < self._max_retries:
                retry_after = _retry_after_seconds(response.headers)
                self._sleeper(retry_after if retry_after is not None else self._backoff_seconds(retry_count))
                continue
            raise ApiError(endpoint, message, response.status_code, context, retry_count, request_id)
        raise AssertionError("Retry loop must return or raise.")

    @staticmethod
    def _backoff_seconds(retry_count: int) -> float:
        return min(0.5 * (2**retry_count), 8.0)


def _request_id(headers: dict[str, str]) -> str | None:
    lowered = {key.lower(): value for key, value in headers.items()}
    return lowered.get("x-request-id") or lowered.get("request-id")


def _retry_after_seconds(headers: dict[str, str]) -> float | None:
    lowered = {key.lower(): value for key, value in headers.items()}
    try:
        return max(float(lowered["retry-after"]), 0.0)
    except (KeyError, ValueError):
        return None


def _error_message(body: bytes) -> str:
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "HTTP request failed."
    if isinstance(decoded, dict) and isinstance(decoded.get("message"), str):
        return decoded["message"]
    return "HTTP request failed."
