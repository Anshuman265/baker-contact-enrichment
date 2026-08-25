"""Lead Finder search endpoint client and response parsing."""

from __future__ import annotations

from typing import Any

from baker_enrichment.api.client import EnrichApiClient
from baker_enrichment.api.contracts import LeadCandidate, LeadFinderPage, Pagination


SEARCH_ENDPOINT = "/api/v3/lead-finder/search"


class LeadFinderClient:
    def __init__(self, api: EnrichApiClient) -> None:
        self._api = api

    def search_all(self, first_name: str, last_name: str, *, context: dict[str, str] | None = None) -> tuple[LeadCandidate, ...]:
        """Fetch every page, stopping solely when Enrich reports `hasMore: false`."""
        candidates: list[LeadCandidate] = []
        page = 1
        request_context = context or {}
        while True:
            result = self.search_page(first_name, last_name, page=page, context=request_context)
            candidates.extend(result.results)
            if not result.pagination.has_more:
                return tuple(candidates)
            page += 1

    def search_page(
        self, first_name: str, last_name: str, *, page: int, context: dict[str, str] | None = None
    ) -> LeadFinderPage:
        response = self._api.post_json(
            SEARCH_ENDPOINT,
            {"filters": {"firstName": first_name, "lastName": last_name}, "page": page, "pageSize": 100},
            context=context or {},
        )
        return parse_lead_finder_page(response)


def parse_lead_finder_page(response: dict[str, Any]) -> LeadFinderPage:
    data = _data_object(response)
    results = data.get("results")
    pagination = data.get("pagination")
    if not isinstance(results, list) or not isinstance(pagination, dict):
        raise ValueError("Lead Finder response requires data.results and data.pagination.")
    return LeadFinderPage(
        results=tuple(_candidate(item) for item in results if isinstance(item, dict)),
        pagination=Pagination(
            page=_integer(pagination, "page"),
            page_size=_integer(pagination, "pageSize"),
            total_results=_integer(pagination, "totalResults"),
            total_pages=_integer(pagination, "totalPages"),
            has_more=_boolean(pagination, "hasMore"),
            searched_total_result=_optional_int(pagination.get("searchedTotalResult")),
        ),
    )


def _candidate(value: dict[str, Any]) -> LeadCandidate:
    candidate_id = value.get("id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ValueError("Lead Finder candidate requires an id.")
    return LeadCandidate(
        id=candidate_id,
        first_name=_optional_string(value.get("firstName")),
        last_name=_optional_string(value.get("lastName")),
        linkedin_url=_optional_string(value.get("linkedinUrl")),
        headline=_optional_string(value.get("headline")),
        job_title=_optional_string(value.get("jobTitle")),
        company_name=_optional_string(value.get("companyName")),
        raw=value,
    )


def _data_object(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    if not isinstance(data, dict):
        raise ValueError("Enrich response requires an object in data.")
    return data


def _integer(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"Expected integer pagination field {key}.")
    return value


def _boolean(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Expected boolean pagination field {key}.")
    return value


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None
