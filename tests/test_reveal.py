import json

from baker_enrichment.api.client import EnrichApiClient
from baker_enrichment.api.reveal import RevealClient
from baker_enrichment.config import EnrichSettings
from tests.api_helpers import QueueTransport, fixture, json_response


def test_reveal_submits_selected_id_then_polls_to_completion() -> None:
    transport = QueueTransport([
        json_response({"success": True, "data": {"jobId": "job-1"}}),
        json_response(fixture("reveal_running.json")),
        json_response(fixture("reveal_completed.json")),
    ])
    waits: list[float] = []
    reveal = RevealClient(EnrichApiClient(EnrichSettings(api_key="test"), transport=transport), sleeper=waits.append)
    job_id = reveal.start("lead-1")
    completed = reveal.poll(job_id, poll_interval_seconds=0.25)
    assert json.loads(transport.requests[0].data.decode()) == {"leadIds": ["lead-1"]}
    assert completed.status == "completed"
    assert completed.revealed[0].preferred_phone == "+1 415-677-1441"
    assert waits == [0.25]
