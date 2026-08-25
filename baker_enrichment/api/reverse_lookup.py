"""Reverse Email Lookup endpoint client and its data-only parser."""

from __future__ import annotations

from typing import Any

from baker_enrichment.api.client import EnrichApiClient
from baker_enrichment.api.contracts import ReverseLookupData


REVERSE_LOOKUP_ENDPOINT = "/api/v3/reverse-lookup/lookup"
PERSON_URN_PREFIX = "urn:li:person:"


class ReverseLookupClient:
    def __init__(self, api: EnrichApiClient) -> None:
        self._api = api

    def lookup(self, email: str, *, context: dict[str, str] | None = None) -> ReverseLookupData:
        response = self._api.post_json(REVERSE_LOOKUP_ENDPOINT, {"email": email}, context=context or {})
        return parse_reverse_lookup(response)


def parse_reverse_lookup(response: dict[str, Any]) -> ReverseLookupData:
    data = response.get("data")
    if not isinstance(data, dict):
        raise ValueError("Reverse Lookup response requires an object in data.")
    string = lambda name: data[name] if isinstance(data.get(name), str) else None
    raw_id = string("id")
    skills = data.get("skills")
    return ReverseLookupData(
        id=raw_id.removeprefix(PERSON_URN_PREFIX) if raw_id else None,
        display_name=string("displayName"), first_name=string("firstName"), last_name=string("lastName"),
        headline=string("headline"), summary=string("summary"), company_name=string("companyName"),
        location=string("location"), photo_url=string("photoUrl"), profile_url=string("profileUrl"),
        report_profile_url=string("reportProfileUrl"),
        connection_count=data.get("connectionCount") if isinstance(data.get("connectionCount"), int) else None,
        is_connection_count_obfuscated=data.get("isConnectionCountObfuscated") if isinstance(data.get("isConnectionCountObfuscated"), bool) else None,
        skills=tuple(skill for skill in skills if isinstance(skill, str)) if isinstance(skills, list) else (),
        locale=data.get("locale") if isinstance(data.get("locale"), dict) else {},
        schools=data.get("schools"), positions=data.get("positions"), public_profile=data.get("publicProfile"), raw=data,
    )
