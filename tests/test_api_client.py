from __future__ import annotations

import socket

import pytest

from baker_enrichment.api.client import ApiError, EnrichApiClient
from baker_enrichment.config import EnrichSettings
from tests.api_helpers import QueueTransport, json_response


def client(transport: QueueTransport, delays: list[float]) -> EnrichApiClient:
    return EnrichApiClient(EnrichSettings(api_key="test-key"), transport=transport, sleeper=delays.append)


def test_retries_429_and_preserves_request_id() -> None:
    transport = QueueTransport([
        json_response({"message": "slow down"}, 429, {"x-request-id": "request-1", "Retry-After": "0"}),
        json_response({"success": True, "data": {}}),
    ])
    delays: list[float] = []
    result = client(transport, delays).get_json("/test", context={"record_id": "row-2"})
    assert result["success"] is True
    assert len(transport.requests) == 2
    assert delays == [0.0]


def test_retries_timeout_then_succeeds() -> None:
    transport = QueueTransport([socket.timeout("timed out"), json_response({"success": True, "data": {}})])
    delays: list[float] = []
    assert client(transport, delays).get_json("/test", context={})["success"] is True
    assert delays == [0.5]


def test_permanent_4xx_is_not_retried_and_is_structured() -> None:
    transport = QueueTransport([json_response({"message": "bad input"}, 400, {"request-id": "r-9"})])
    with pytest.raises(ApiError) as raised:
        client(transport, []).post_json("/test", {}, context={"record_id": "row-4"})
    error = raised.value
    assert (error.endpoint, error.status_code, error.request_context, error.retry_count, error.request_id) == (
        "/test", 400, {"record_id": "row-4"}, 0, "r-9"
    )
    assert len(transport.requests) == 1


def test_exhausted_5xx_retries_are_bounded() -> None:
    transport = QueueTransport([json_response({}, 503) for _ in range(4)])
    delays: list[float] = []
    with pytest.raises(ApiError) as raised:
        client(transport, delays).get_json("/test", context={})
    assert raised.value.retry_count == 3
    assert len(transport.requests) == 4
    assert delays == [0.5, 1.0, 2.0]


def test_success_false_is_an_api_error() -> None:
    transport = QueueTransport([json_response({"success": False, "data": {}})])
    with pytest.raises(ApiError, match="success=false"):
        client(transport, []).get_json("/test", context={})
