import json

from baker_enrichment.api.client import EnrichApiClient, HttpResponse
from baker_enrichment.api.lead_finder import LeadFinderClient
from baker_enrichment.config import EnrichSettings
from tests.api_helpers import QueueTransport, fixture, json_response


def test_search_follows_has_more_and_collects_all_candidates() -> None:
    transport = QueueTransport([json_response(fixture("lead_finder_page_1.json")), json_response(fixture("lead_finder_page_2.json"))])
    candidates = LeadFinderClient(EnrichApiClient(EnrichSettings(api_key="test"), transport=transport)).search_all("Kabeer", "Chopra")
    assert [candidate.id for candidate in candidates] == ["lead-1", "lead-2"]
    assert [json.loads(request.data.decode())["page"] for request in transport.requests] == [1, 2]
    assert all(json.loads(request.data.decode())["pageSize"] == 100 for request in transport.requests)
