"""Bounded, read-only operations over one validated case bundle."""

from __future__ import annotations

from collections.abc import Sequence

from boring_triage.domain import (
    CaseBundle,
    CaseOverview,
    EvidenceRecord,
    EvidenceSearch,
    ResourceContext,
    TimelineEntry,
)
from boring_triage.errors import EvidenceNotFoundError, QueryError


class EvidenceService:
    """Expose case-scoped evidence without arbitrary query or filesystem access."""

    def __init__(self, bundle: CaseBundle) -> None:
        self._bundle = bundle
        self._evidence_by_id = {record.evidence_id: record for record in bundle.evidence}
        self._resources_by_id = {resource.resource_id: resource for resource in bundle.resources}

    def get_case_overview(self) -> CaseOverview:
        manifest = self._bundle.manifest
        return CaseOverview(
            case_id=manifest.case_id,
            title=manifest.title,
            description=manifest.description,
            start_time=manifest.start_time,
            end_time=manifest.end_time,
            source_types=tuple(
                sorted({record.source_type for record in self._bundle.evidence}, key=lambda item: item.value)
            ),
            resource_ids=tuple(sorted(self._resources_by_id)),
            evidence_count=len(self._bundle.evidence),
        )

    def search_evidence(self, query: EvidenceSearch) -> tuple[EvidenceRecord, ...]:
        manifest = self._bundle.manifest
        if query.limit > manifest.max_search_results:
            raise QueryError(f"search limit exceeds case maximum of {manifest.max_search_results}")
        if query.start_time and query.start_time < manifest.start_time:
            raise QueryError("search start_time is outside the case window")
        if query.end_time and query.end_time > manifest.end_time:
            raise QueryError("search end_time is outside the case window")

        records = sorted(self._bundle.evidence, key=lambda item: (item.observed_at, item.evidence_id))
        matches: list[EvidenceRecord] = []
        for record in records:
            if query.source_type and record.source_type != query.source_type:
                continue
            if query.start_time and record.observed_at < query.start_time:
                continue
            if query.end_time and record.observed_at > query.end_time:
                continue
            if query.event_category and record.event_category != query.event_category:
                continue
            if query.source_address and record.attributes.get("src_addr") != query.source_address:
                continue
            if query.destination_address and record.attributes.get("dst_addr") != query.destination_address:
                continue
            if query.actor_or_resource_id:
                actor = record.attributes.get("actor_id")
                if query.actor_or_resource_id not in record.resource_ids and actor != query.actor_or_resource_id:
                    continue
            matches.append(record)
            if len(matches) == query.limit:
                break
        return tuple(matches)

    def get_evidence_records(self, evidence_ids: Sequence[str]) -> tuple[EvidenceRecord, ...]:
        if not evidence_ids:
            raise QueryError("at least one evidence ID is required")
        if len(evidence_ids) > self._bundle.manifest.max_record_details:
            maximum = self._bundle.manifest.max_record_details
            raise QueryError(f"record request exceeds case maximum of {maximum}")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise QueryError("evidence IDs must not contain duplicates")

        missing = [evidence_id for evidence_id in evidence_ids if evidence_id not in self._evidence_by_id]
        if missing:
            raise EvidenceNotFoundError(f"unknown evidence ID: {missing[0]}")
        return tuple(self._evidence_by_id[evidence_id] for evidence_id in evidence_ids)

    def get_resource_context(self, resource_id: str) -> ResourceContext:
        try:
            return self._resources_by_id[resource_id]
        except KeyError as error:
            raise EvidenceNotFoundError(f"unknown resource ID: {resource_id}") from error

    def timeline(self) -> tuple[TimelineEntry, ...]:
        records = sorted(self._bundle.evidence, key=lambda item: (item.observed_at, item.evidence_id))
        return tuple(
            TimelineEntry(
                evidence_id=record.evidence_id,
                observed_at=record.observed_at,
                source_type=record.source_type,
                event_category=record.event_category,
                summary=record.summary,
            )
            for record in records
        )
