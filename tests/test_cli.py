from pathlib import Path

from baker_enrichment.cli import main


def test_dry_run_validates_a_local_input_without_api_key(tmp_path: Path, monkeypatch) -> None:
    workbook = tmp_path / "baker.xlsx"
    workbook.touch()
    monkeypatch.delenv("ENRICH_API_KEY", raising=False)
    assert main(["run", "--input", str(workbook), "--dry-run"]) == 0


def test_real_run_fails_clearly_without_api_key(tmp_path: Path, monkeypatch) -> None:
    workbook = tmp_path / "baker.xlsx"
    workbook.touch()
    monkeypatch.delenv("ENRICH_API_KEY", raising=False)
    assert main(["run", "--input", str(workbook)]) == 2


def test_structured_logs_keep_non_sensitive_context(caplog) -> None:
    # The formatter redacts sensitive keys while preserving operational context.
    from baker_enrichment.logging import JsonFormatter
    import logging

    record = logging.LogRecord("test", logging.INFO, "", 0, "event", (), None)
    record.context = {"record_id": "row-2", "email": "private@example.test"}
    rendered = JsonFormatter().format(record)
    assert '"record_id": "row-2"' in rendered
    assert '"email": "[redacted]"' in rendered
