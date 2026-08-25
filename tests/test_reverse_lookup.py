import json

from baker_enrichment.api.client import EnrichApiClient
from baker_enrichment.api.reverse_lookup import ReverseLookupClient
from baker_enrichment.config import EnrichSettings
from tests.api_helpers import QueueTransport, fixture, json_response


def test_reverse_lookup_uses_data_only_and_strips_person_urn() -> None:
    transport = QueueTransport([json_response(fixture("reverse_lookup.json"))])
    result = ReverseLookupClient(EnrichApiClient(EnrichSettings(api_key="test"), transport=transport)).lookup("private@example.test")
    assert result.id == "DgE_61zIs3q"
    assert result.skills == ("Mathematics", "Programming")
    assert "meta" not in result.raw
    assert json.loads(transport.requests[0].data.decode()) == {"email": "private@example.test"}
