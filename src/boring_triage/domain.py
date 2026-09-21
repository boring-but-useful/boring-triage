"""Strict domain models for synthetic incident evidence."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from ipaddress import ip_address
from pathlib import Path
from typing import Annotated, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

JsonScalar: TypeAlias = str | int | float | bool | None
AttributeValue: TypeAlias = JsonScalar | list[JsonScalar]

CaseId = Annotated[str, Field(pattern=r"^case-[a-z0-9-]+$", min_length=8, max_length=80)]
EvidenceId = Annotated[str, Field(pattern=r"^ev-[0-9]{4}$")]
ResourceId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{2,79}$")]


class StrictModel(BaseModel):
    """Reject undeclared fields and prevent accidental mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceType(str, Enum):
    CLOUDTRAIL = "cloudtrail"
    VPC_FLOW_LOG = "vpc_flow_log"
    GUARDDUTY = "guardduty"
    IAM_SNAPSHOT = "iam_snapshot"
    NETWORK_SNAPSHOT = "network_snapshot"
    WORKLOAD_METADATA = "workload_metadata"


class EventCategory(str, Enum):
    IDENTITY_SESSION = "identity_session"
    API_ACTIVITY = "api_activity"
    NETWORK_CONNECTION = "network_connection"
    DETECTION = "detection"
    PERMISSIONS = "permissions"
    NETWORK_CONFIGURATION = "network_configuration"
    WORKLOAD_CONTEXT = "workload_context"


class TrustLevel(str, Enum):
    UNTRUSTED_INPUT = "untrusted_input"


def _require_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return value


def _validate_attributes(value: dict[str, AttributeValue]) -> dict[str, AttributeValue]:
    if len(value) > 50:
        raise ValueError("attributes may contain at most 50 fields")
    for name, attribute in value.items():
        if not name or len(name) > 80 or not name.replace("_", "").isalnum():
            raise ValueError("attribute names must contain only letters, digits, and underscores")
        values = attribute if isinstance(attribute, list) else [attribute]
        if len(values) > 100:
            raise ValueError("attribute lists may contain at most 100 values")
        if any(isinstance(item, str) and len(item) > 1_000 for item in values):
            raise ValueError("attribute strings may contain at most 1000 characters")
    return value


class CaseManifest(StrictModel):
    case_id: CaseId
    version: Annotated[int, Field(ge=1)]
    title: Annotated[str, Field(min_length=1, max_length=160)]
    description: Annotated[str, Field(min_length=1, max_length=1_000)]
    start_time: datetime
    end_time: datetime
    evidence_file: str
    resource_context_file: str
    max_search_results: Annotated[int, Field(ge=1, le=100)] = 25
    max_record_details: Annotated[int, Field(ge=1, le=50)] = 10

    @field_validator("start_time", "end_time")
    @classmethod
    def timestamps_are_aware(cls, value: datetime) -> datetime:
        return _require_aware(value)

    @field_validator("evidence_file", "resource_context_file")
    @classmethod
    def data_files_are_local_json_names(cls, value: str) -> str:
        path = Path(value)
        if path.name != value or path.suffix != ".json" or value in {".", ".."}:
            raise ValueError("data file must be a local .json filename")
        return value

    @model_validator(mode="after")
    def time_window_is_ordered(self) -> CaseManifest:
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        if self.evidence_file == self.resource_context_file:
            raise ValueError("evidence and resource context must use separate files")
        return self


class EvidenceRecord(StrictModel):
    evidence_id: EvidenceId
    case_id: CaseId
    source_type: SourceType
    observed_at: datetime
    resource_ids: Annotated[tuple[ResourceId, ...], Field(min_length=1, max_length=20)]
    event_category: EventCategory
    summary: Annotated[str, Field(min_length=1, max_length=500)]
    attributes: dict[str, AttributeValue]
    trust: TrustLevel = TrustLevel.UNTRUSTED_INPUT

    @field_validator("observed_at")
    @classmethod
    def timestamp_is_aware(cls, value: datetime) -> datetime:
        return _require_aware(value)

    @field_validator("resource_ids")
    @classmethod
    def resource_ids_are_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("resource_ids must be unique")
        return value

    @field_validator("attributes")
    @classmethod
    def attribute_names_are_safe(cls, value: dict[str, AttributeValue]) -> dict[str, AttributeValue]:
        return _validate_attributes(value)


class ResourceContext(StrictModel):
    resource_id: ResourceId
    case_id: CaseId
    resource_type: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{2,49}$")]
    observed_at: datetime
    attributes: dict[str, AttributeValue]
    trust: TrustLevel = TrustLevel.UNTRUSTED_INPUT

    @field_validator("observed_at")
    @classmethod
    def timestamp_is_aware(cls, value: datetime) -> datetime:
        return _require_aware(value)

    @field_validator("attributes")
    @classmethod
    def attribute_names_are_safe(cls, value: dict[str, AttributeValue]) -> dict[str, AttributeValue]:
        return _validate_attributes(value)


class EvidenceFile(StrictModel):
    records: Annotated[tuple[EvidenceRecord, ...], Field(min_length=1, max_length=1_000)]


class ResourceContextFile(StrictModel):
    resources: Annotated[tuple[ResourceContext, ...], Field(min_length=1, max_length=500)]


class CaseBundle(StrictModel):
    manifest: CaseManifest
    evidence: tuple[EvidenceRecord, ...]
    resources: tuple[ResourceContext, ...]


class EvidenceSearch(StrictModel):
    source_type: SourceType | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    actor_or_resource_id: Annotated[
        str | None,
        Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._:@/-]+$"),
    ] = None
    source_address: Annotated[str | None, Field(min_length=1, max_length=64)] = None
    destination_address: Annotated[str | None, Field(min_length=1, max_length=64)] = None
    event_category: EventCategory | None = None
    limit: Annotated[int, Field(ge=1, le=100)] = 20

    @field_validator("start_time", "end_time")
    @classmethod
    def optional_timestamps_are_aware(cls, value: datetime | None) -> datetime | None:
        return _require_aware(value) if value is not None else None

    @field_validator("source_address", "destination_address")
    @classmethod
    def addresses_are_ip_literals(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return str(ip_address(value))
        except ValueError as error:
            raise ValueError("address must be an IPv4 or IPv6 literal") from error

    @model_validator(mode="after")
    def optional_time_window_is_ordered(self) -> EvidenceSearch:
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("start_time must be at or before end_time")
        return self


class CaseOverview(StrictModel):
    case_id: CaseId
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    source_types: tuple[SourceType, ...]
    resource_ids: tuple[ResourceId, ...]
    evidence_count: int


class TimelineEntry(StrictModel):
    evidence_id: EvidenceId
    observed_at: datetime
    source_type: SourceType
    event_category: EventCategory
    summary: str
