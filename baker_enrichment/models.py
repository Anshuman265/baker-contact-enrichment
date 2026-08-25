"""Typed, provenance-preserving domain models used across pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MatchMethod(StrEnum):
    EXACT_LINKEDIN = "exact_linkedin"
    LLM_FALLBACK = "llm_fallback"
    NO_MATCH = "no_match"


class RecordStatus(StrEnum):
    PENDING = "pending"
    ENRICHED = "enriched"
    REVIEW_REQUIRED = "review_required"
    FAILED = "failed"
    NO_MATCH = "no_match"


@dataclass(frozen=True, slots=True)
class BakerRecord:
    record_id: str
    row_number: int
    first_name: str | None
    last_name: str | None
    linkedin_url: str | None
    email: str | None
    phone: str | None
    original_values: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RoleCompanyPair:
    title: str | None
    company: str | None
    source: str
    evidence: str | None = None


@dataclass(frozen=True, slots=True)
class ProvenancedValue:
    value: Any
    source: str


@dataclass(slots=True)
class EnrichmentResult:
    record: BakerRecord
    status: RecordStatus = RecordStatus.PENDING
    selected_lead_id: str | None = None
    match_method: MatchMethod | None = None
    confidence: float | None = None
    matching_reason: str | None = None
    needs_review: bool = False
    field_provenance: dict[str, ProvenancedValue] = field(default_factory=dict)
    role_pairs: list[RoleCompanyPair] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class EnrichedContact:
    """Baker-facing row with deterministic, intentionally non-debug column fields."""

    lead_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email_domain: str | None = None
    linkedin_profile: str | None = None
    headline: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    skill: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    company_domain: str | None = None
    company_linkedin: str | None = None
    employee_count: int | None = None
    sic_industry_classification: str | None = None
    naics_industry_classification: str | None = None
    revenue: str | None = None
    specialties: str | None = None
    founded_year: int | None = None
    hq_city: str | None = None
    hq_state: str | None = None
    hq_country: str | None = None
    last_funding_type: str | None = None
    last_funding_date: str | None = None
    email: str | None = None
    phone: str | None = None


@dataclass(frozen=True, slots=True)
class ReverseLookupRow:
    id: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    headline: str | None = None
    current_role: str | None = None
    current_company: str | None = None
    summary: str | None = None
    company: str | None = None
    location: str | None = None
    photo_url: str | None = None
    profile_url: str | None = None
    report_profile_url: str | None = None
    connection_count: int | None = None
    connections_obfuscated: bool | None = None
    public_profile: str | None = None
    lookup_email: str | None = None
    skills: str | None = None
    locale_country: str | None = None
    locale_language: str | None = None
    education: str | None = None
    work_history: str | None = None


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    original_record: BakerRecord
    candidate_data: dict[str, Any] | None
    selected_lead_id: str | None
    confidence: float | None
    matching_method: str | None
    evidence: str | None
    conflict: str | None
    recommended_action: str


@dataclass(frozen=True, slots=True)
class FailedRecord:
    original_record: BakerRecord
    stage: str
    error: str


@dataclass(frozen=True, slots=True)
class RunReport:
    metrics: dict[str, int | float | str | None]
