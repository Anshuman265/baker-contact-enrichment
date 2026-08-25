"""Response contracts for Enrich endpoints; no network behavior lives here."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LeadCandidate:
    id: str
    first_name: str | None = None
    last_name: str | None = None
    linkedin_url: str | None = None
    headline: str | None = None
    job_title: str | None = None
    company_name: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Pagination:
    page: int
    page_size: int
    total_results: int
    total_pages: int
    has_more: bool
    searched_total_result: int | None = None


@dataclass(frozen=True, slots=True)
class LeadFinderPage:
    results: tuple[LeadCandidate, ...]
    pagination: Pagination


@dataclass(frozen=True, slots=True)
class RevealedContact:
    id: str
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    company_name: str | None = None
    email_address: str | None = None
    phone: str | None = None
    cellphone: str | None = None
    linkedin_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def preferred_phone(self) -> str | None:
        return self.phone or self.cellphone


@dataclass(frozen=True, slots=True)
class RevealJob:
    job_id: str
    status: str
    revealed: tuple[RevealedContact, ...] = ()


@dataclass(frozen=True, slots=True)
class ReverseLookupData:
    id: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    headline: str | None = None
    summary: str | None = None
    company_name: str | None = None
    location: str | None = None
    photo_url: str | None = None
    profile_url: str | None = None
    report_profile_url: str | None = None
    connection_count: int | None = None
    is_connection_count_obfuscated: bool | None = None
    skills: tuple[str, ...] = ()
    locale: dict[str, Any] = field(default_factory=dict)
    schools: Any = None
    positions: Any = None
    public_profile: Any = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMSelection:
    selected_id: str | None
    confidence: float
    reason: str
    needs_review: bool
