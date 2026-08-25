"""Command-line interface contract for the Baker enrichment application."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from baker_enrichment.config import ConfigurationError, Settings
from baker_enrichment.excel import WorkbookValidationError, validate_baker_workbook
from baker_enrichment.logging import configure_logging, log_event

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="baker-enrichment")
    parser.add_argument("--verbose", action="store_true", help="Emit debug-level structured logs.")
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="Validate and execute an enrichment run.")
    run.add_argument("--input", required=True, type=Path, help="Path to the Baker .xlsx workbook.")
    run.add_argument("--output-dir", type=Path, default=Path("output"))
    run.add_argument("--dry-run", action="store_true", help="Validate locally without network calls.")
    run.add_argument("--limit", type=_positive_int, help="Process at most this many records.")

    resume = commands.add_parser("resume", help="Resume a checkpointed enrichment run.")
    resume.add_argument("--run-id", required=True)
    resume.add_argument("--output-dir", type=Path, default=Path("output"))
    validate = commands.add_parser("validate", help="Validate a Baker workbook without API calls.")
    validate.add_argument("--input", required=True, type=Path, help="Path to the Baker .xlsx workbook.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)
    if args.command == "validate":
        try:
            mapping = validate_baker_workbook(args.input)
        except (OSError, WorkbookValidationError) as error:
            LOGGER.error("Workbook validation failed: %s", error)
            return 2
        log_event(LOGGER, logging.INFO, "workbook_validated", detected_columns=sorted(key for key, value in mapping.columns.items() if value))
        return 0

    settings = Settings.from_environment()
    try:
        settings.validate(require_enrich_api_key=not getattr(args, "dry_run", False))
    except ConfigurationError as error:
        LOGGER.error(str(error))
        return 2

    if args.command == "run":
        if not args.input.is_file():
            LOGGER.error("Input workbook does not exist: %s", args.input)
            return 2
        if args.dry_run:
            log_event(LOGGER, logging.INFO, "dry_run_validated", input=str(args.input))
            return 0
        LOGGER.error("Pipeline orchestration is not implemented in the foundation phase.")
        return 3

    LOGGER.error("Checkpoint resume is not implemented in the foundation phase.")
    return 3


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed
