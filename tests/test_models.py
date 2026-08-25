from baker_enrichment.api.contracts import RevealedContact
from baker_enrichment.models import BakerRecord, EnrichmentResult, RecordStatus


def test_reveal_prefers_phone_over_cellphone() -> None:
    assert RevealedContact(id="lead-1", phone="111", cellphone="222").preferred_phone == "111"
    assert RevealedContact(id="lead-1", cellphone="222").preferred_phone == "222"


def test_result_keeps_original_record_and_defaults_to_pending() -> None:
    record = BakerRecord("row-2", 2, "Ada", "Lovelace", None, None, None, {})
    result = EnrichmentResult(record=record)
    assert result.record is record
    assert result.status is RecordStatus.PENDING
