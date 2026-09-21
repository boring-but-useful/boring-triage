"""Human-gated investigation models and orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Protocol

from pydantic import Field, model_validator

from boring_triage.domain import (
    CaseId,
    CaseOverview,
    EvidenceId,
    EvidenceRecord,
    EvidenceSearch,
    ResourceContext,
    ResourceId,
    StrictModel,
)
from boring_triage.errors import ApprovalRequiredError, InvalidModelOutputError
from boring_triage.tools import EvidenceService

CallId = Annotated[str, Field(pattern=r"^call-[0-9]{4}$")]


class EvidenceOperation(StrEnum):
    SEARCH_EVIDENCE = "search_evidence"
    GET_EVIDENCE_RECORDS = "get_evidence_records"
    GET_RESOURCE_CONTEXT = "get_resource_context"


class ModelProvider(StrEnum):
    FAKE = "fake"
    OPENAI = "openai"


class PlannedEvidenceCall(StrictModel):
    call_id: CallId
    purpose: Annotated[str, Field(min_length=1, max_length=240)]
    operation: EvidenceOperation
    query: EvidenceSearch | None = None
    evidence_ids: (
        Annotated[tuple[EvidenceId, ...], Field(min_length=1, max_length=10)] | None
    ) = None
    resource_id: ResourceId | None = None

    @model_validator(mode="after")
    def arguments_match_operation(self) -> PlannedEvidenceCall:
        supplied = {
            "query": self.query is not None,
            "evidence_ids": self.evidence_ids is not None,
            "resource_id": self.resource_id is not None,
        }
        required = {
            EvidenceOperation.SEARCH_EVIDENCE: "query",
            EvidenceOperation.GET_EVIDENCE_RECORDS: "evidence_ids",
            EvidenceOperation.GET_RESOURCE_CONTEXT: "resource_id",
        }[self.operation]
        if not supplied[required] or sum(supplied.values()) != 1:
            raise ValueError("tool arguments do not match the selected operation")
        return self


class InvestigationPlan(StrictModel):
    rationale: Annotated[str, Field(min_length=1, max_length=1_000)]
    calls: Annotated[tuple[PlannedEvidenceCall, ...], Field(min_length=1, max_length=8)]

    @model_validator(mode="after")
    def call_ids_are_unique(self) -> InvestigationPlan:
        call_ids = [call.call_id for call in self.calls]
        if len(call_ids) != len(set(call_ids)):
            raise ValueError("plan call IDs must be unique")
        return self


class PlanArtifact(StrictModel):
    case_id: CaseId
    provider: ModelProvider
    model: Annotated[str, Field(min_length=1, max_length=100)]
    proposed_at: datetime
    plan: InvestigationPlan


class ToolExecution(StrictModel):
    call_id: CallId
    operation: EvidenceOperation
    evidence_records: tuple[EvidenceRecord, ...] = ()
    resource_context: ResourceContext | None = None

    @model_validator(mode="after")
    def result_matches_operation(self) -> ToolExecution:
        is_resource_call = self.operation == EvidenceOperation.GET_RESOURCE_CONTEXT
        if is_resource_call != (self.resource_context is not None):
            raise ValueError("tool result does not match its operation")
        if is_resource_call and self.evidence_records:
            raise ValueError("resource lookup cannot return evidence records")
        return self


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CitedFact(StrictModel):
    statement: Annotated[str, Field(min_length=1, max_length=500)]
    evidence_ids: Annotated[tuple[EvidenceId, ...], Field(min_length=1, max_length=10)]


class Hypothesis(StrictModel):
    statement: Annotated[str, Field(min_length=1, max_length=500)]
    confidence: Confidence
    evidence_ids: Annotated[tuple[EvidenceId, ...], Field(min_length=1, max_length=10)]


class RecommendedDisposition(StrEnum):
    CONTINUE = "continue_investigation"
    ESCALATE = "escalate"
    CLOSE_EXPECTED = "close_expected_behavior"


class Recommendation(StrictModel):
    disposition: RecommendedDisposition
    rationale: Annotated[str, Field(min_length=1, max_length=800)]
    evidence_ids: Annotated[tuple[EvidenceId, ...], Field(min_length=1, max_length=10)]


class InvestigationAnalysis(StrictModel):
    facts: Annotated[tuple[CitedFact, ...], Field(min_length=1, max_length=12)]
    hypotheses: Annotated[tuple[Hypothesis, ...], Field(max_length=8)] = ()
    unknowns: Annotated[
        tuple[Annotated[str, Field(min_length=1, max_length=400)], ...],
        Field(max_length=12),
    ] = ()
    recommendation: Recommendation


class HumanDecision(StrictModel):
    disposition: RecommendedDisposition
    note: Annotated[str, Field(min_length=1, max_length=1_000)]
    decided_by: Annotated[str, Field(min_length=1, max_length=100)]
    decided_at: datetime


class InvestigationRecord(StrictModel):
    case_id: CaseId
    provider: str
    model: str
    approved_by: Annotated[str, Field(min_length=1, max_length=100)]
    approved_at: datetime
    plan: InvestigationPlan
    tool_executions: tuple[ToolExecution, ...]
    analysis: InvestigationAnalysis
    human_decision: HumanDecision


class ModelAdapter(Protocol):
    provider_name: ModelProvider
    model_name: str

    def propose_plan(self, overview: CaseOverview) -> InvestigationPlan: ...

    def analyze(
        self,
        overview: CaseOverview,
        plan: InvestigationPlan,
        results: Sequence[ToolExecution],
    ) -> InvestigationAnalysis: ...


class InvestigationOrchestrator:
    """Keep approval, evidence execution, and citation checks outside the model."""

    def __init__(self, service: EvidenceService, adapter: ModelAdapter) -> None:
        self._service = service
        self._adapter = adapter

    def propose_plan(self) -> PlanArtifact:
        overview = self._service.get_case_overview()
        return PlanArtifact(
            case_id=overview.case_id,
            provider=self._adapter.provider_name,
            model=self._adapter.model_name,
            proposed_at=datetime.now(UTC),
            plan=self._adapter.propose_plan(overview),
        )

    def execute_approved_plan(
        self,
        artifact: PlanArtifact,
        *,
        approved: bool,
        approved_by: str,
        disposition: RecommendedDisposition,
        decision_note: str,
    ) -> InvestigationRecord:
        overview = self._service.get_case_overview()
        if not approved:
            raise ApprovalRequiredError("the saved investigation plan was not approved")
        if artifact.case_id != overview.case_id:
            raise ApprovalRequiredError("approved plan belongs to a different case")
        if artifact.provider != self._adapter.provider_name:
            raise ApprovalRequiredError("approved plan belongs to a different provider")
        if artifact.model != self._adapter.model_name:
            raise ApprovalRequiredError("approved plan belongs to a different model")

        approved_at = datetime.now(UTC)
        results = tuple(self._execute(call) for call in artifact.plan.calls)
        analysis = self._adapter.analyze(overview, artifact.plan, results)
        self._validate_citations(analysis, results)
        decided_at = datetime.now(UTC)
        return InvestigationRecord(
            case_id=overview.case_id,
            provider=artifact.provider,
            model=artifact.model,
            approved_by=approved_by,
            approved_at=approved_at,
            plan=artifact.plan,
            tool_executions=results,
            analysis=analysis,
            human_decision=HumanDecision(
                disposition=disposition,
                note=decision_note,
                decided_by=approved_by,
                decided_at=decided_at,
            ),
        )

    def _execute(self, call: PlannedEvidenceCall) -> ToolExecution:
        if call.operation == EvidenceOperation.SEARCH_EVIDENCE:
            if call.query is None:
                raise InvalidModelOutputError("search call is missing its query")
            records = self._service.search_evidence(call.query)
            return ToolExecution(
                call_id=call.call_id,
                operation=call.operation,
                evidence_records=records,
            )
        if call.operation == EvidenceOperation.GET_EVIDENCE_RECORDS:
            if call.evidence_ids is None:
                raise InvalidModelOutputError("record call is missing evidence IDs")
            records = self._service.get_evidence_records(call.evidence_ids)
            return ToolExecution(
                call_id=call.call_id,
                operation=call.operation,
                evidence_records=records,
            )
        if call.resource_id is None:
            raise InvalidModelOutputError("resource call is missing its resource ID")
        resource = self._service.get_resource_context(call.resource_id)
        return ToolExecution(
            call_id=call.call_id,
            operation=call.operation,
            resource_context=resource,
        )

    @staticmethod
    def _validate_citations(
        analysis: InvestigationAnalysis, results: Sequence[ToolExecution]
    ) -> None:
        available = {
            record.evidence_id
            for result in results
            for record in result.evidence_records
        }
        cited = {
            evidence_id for fact in analysis.facts for evidence_id in fact.evidence_ids
        }
        cited.update(
            evidence_id
            for hypothesis in analysis.hypotheses
            for evidence_id in hypothesis.evidence_ids
        )
        cited.update(analysis.recommendation.evidence_ids)
        unknown = sorted(cited - available)
        if unknown:
            raise InvalidModelOutputError(
                f"analysis cites evidence not returned by the approved plan: {unknown[0]}"
            )
