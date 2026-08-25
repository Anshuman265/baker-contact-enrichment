"""Reveal job submission and polling, kept independent from orchestration."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from baker_enrichment.api.client import EnrichApiClient
from baker_enrichment.api.contracts import RevealJob, RevealedContact


REVEAL_ENDPOINT = "/api/v3/lead-finder/reveal"
REVEAL_JOB_ENDPOINT = "/api/v3/lead-finder/reveal-jobs/{job_id}"
TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})


class RevealClient:
    def __init__(self, api: EnrichApiClient, *, sleeper: Callable[[float], None] = time.sleep) -> None:
        self._api = api
        self._sleeper = sleeper

    def start(self, lead_id: str, *, context: dict[str, str] | None = None) -> str:
        """Start a reveal job for one selected Lead Finder identifier."""
        response = self._api.post_json(
            REVEAL_ENDPOINT, {"leadIds": [lead_id]}, context=context or {"lead_id": lead_id}
        )
        data = _data_object(response)
        job_id = data.get("jobId")
        if not isinstance(job_id, str) or not job_id:
            raise ValueError("Reveal response requires data.jobId.")
        return job_id

    def poll(
        self, job_id: str, *, poll_interval_seconds: float = 1.0, context: dict[str, str] | None = None
    ) -> RevealJob:
        request_context = context or {"job_id": job_id}
        while True:
            response = self._api.get_json(REVEAL_JOB_ENDPOINT.format(job_id=job_id), context=request_context)
            job = parse_reveal_job(response, job_id=job_id)
            if job.status.lower() in TERMINAL_STATUSES:
                return job
            self._sleeper(poll_interval_seconds)


def parse_reveal_job(response: dict[str, Any], *, job_id: str) -> RevealJob:
    data = _data_object(response)
    status = data.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError("Reveal job response requires data.status.")
    results = data.get("results", {})
    revealed = results.get("revealed", []) if isinstance(results, dict) else []
    if not isinstance(revealed, list):
        raise ValueError("Reveal job data.results.revealed must be a list.")
    return RevealJob(job_id=job_id, status=status, revealed=tuple(_contact(item) for item in revealed if isinstance(item, dict)))


def _contact(value: dict[str, Any]) -> RevealedContact:
    lead_id = value.get("id")
    if not isinstance(lead_id, str) or not lead_id:
        raise ValueError("Revealed contact requires an id.")
    string = lambda name: value[name] if isinstance(value.get(name), str) else None
    return RevealedContact(
        id=lead_id, first_name=string("firstName"), last_name=string("lastName"),
        job_title=string("jobTitle"), company_name=string("companyName"),
        email_address=string("emailAddress"), phone=string("phone"), cellphone=string("cellphone"),
        linkedin_url=string("linkedinUrl"), raw=value,
    )


def _data_object(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    if not isinstance(data, dict):
        raise ValueError("Enrich response requires an object in data.")
    return data
