# Baker Contact Enrichment

A standalone, resumable contact-enrichment application for Baker spreadsheets. It is
being built independently of any exploratory notebook. Credentials are read only
from environment variables and are never written to logs, caches, or output files.

## Current implementation status

The application has package/configuration/logging foundations, independent Enrich API
clients, and a typed Excel import/export layer. The API behavior is covered with
local fixtures and an injectable transport; tests do not contact Enrich. Pipeline
orchestration is intentionally not implemented yet, so the CLI still cannot run a
real enrichment job.

## Configuration

```bash
export ENRICH_API_KEY='replace-with-your-key'
export ENRICH_BASE_URL='https://dev.enrich.so' # optional; this is the default
export BAKER_LLM_PROVIDER=''
export BAKER_LLM_API_KEY=''
export BAKER_LLM_MODEL=''
```

`ENRICH_API_KEY` is required for a real run. If an LLM provider is configured, both
`BAKER_LLM_API_KEY` and `BAKER_LLM_MODEL` must also be configured.

## Intended CLI

```bash
python -m baker_enrichment run --input baker.xlsx --output-dir output
python -m baker_enrichment run --input baker.xlsx --output-dir output --dry-run
python -m baker_enrichment run --input baker.xlsx --output-dir output --limit 5
python -m baker_enrichment resume --run-id <run_id>
python -m baker_enrichment validate --input baker.xlsx
```

`validate` reads and validates a workbook locally and never makes an API call. The
other command forms are present now; orchestration will be added in later phases.
