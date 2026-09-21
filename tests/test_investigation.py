from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from pydantic import ValidationError

from boring_triage.domain import CaseOverview
from boring_triage.errors import ApprovalRequiredError, InvalidModelOutputError
from boring_triage.fixtures import load_case
from boring_triage.investigation import (
    CitedFact,
    EvidenceOperation,
    InvestigationAnalysis,
    InvestigationOrchestrator,
    InvestigationPlan,
    PlannedEvidenceCall,
    Recommendation,
    RecommendedDisposition,
    ToolExecution,
)
from boring_triage.model import FakeModelAdapter
from boring_triage.tools import EvidenceService

CASE_DIRECTORY = Path(__file__).parents[1] / "fixtures" / "case-egress-001"


def _orchestrator(adapter: FakeModelAdapter) -> InvestigationOrchestrator:
    return InvestigationOrchestrator(
        EvidenceService(load_case(CASE_DIRECTORY)), adapter
    )


def test_fake_flow_preserves_ai_and_human_decisions_separately() -> None:
    orchestrator = _orchestrator(FakeModelAdapter())
    artifact = orchestrator.propose_plan()

    record = orchestrator.execute_approved_plan(
        artifact,
        approved=True,
        approved_by="test-analyst",
        disposition=RecommendedDisposition.CONTINUE,
        decision_note="Collect process telemetry before deciding.",
    )

    assert record.analysis.recommendation.disposition == RecommendedDisposition.ESCALATE
    assert record.human_decision.disposition == RecommendedDisposition.CONTINUE
    returned_ids = {
        item.evidence_id
        for execution in record.tool_executions
        for item in execution.evidence_records
    }
    assert "ev-0004" in returned_ids


def test_unapproved_plan_executes_nothing() -> None:
    adapter = FakeModelAdapter()
    orchestrator = _orchestrator(adapter)
    artifact = orchestrator.propose_plan()

    with pytest.raises(ApprovalRequiredError, match="not approved"):
        orchestrator.execute_approved_plan(
            artifact,
            approved=False,
            approved_by="test-analyst",
            disposition=RecommendedDisposition.CONTINUE,
            decision_note="No execution was authorized.",
        )


class InvalidCitationAdapter(FakeModelAdapter):
    def analyze(
        self,
        overview: CaseOverview,
        plan: InvestigationPlan,
        results: Sequence[ToolExecution],
    ) -> InvestigationAnalysis:
        return InvestigationAnalysis(
            facts=(
                CitedFact(
                    statement="This fact cites a record that was never returned.",
                    evidence_ids=("ev-9999",),
                ),
            ),
            recommendation=Recommendation(
                disposition=RecommendedDisposition.CONTINUE,
                rationale="The invalid citation must fail closed.",
                evidence_ids=("ev-9999",),
            ),
        )


def test_analysis_with_unavailable_citation_fails_closed() -> None:
    orchestrator = _orchestrator(InvalidCitationAdapter())
    artifact = orchestrator.propose_plan()

    with pytest.raises(InvalidModelOutputError, match="not returned"):
        orchestrator.execute_approved_plan(
            artifact,
            approved=True,
            approved_by="test-analyst",
            disposition=RecommendedDisposition.CONTINUE,
            decision_note="This record must not be created.",
        )


def test_plan_cannot_be_executed_by_a_different_provider() -> None:
    orchestrator = _orchestrator(FakeModelAdapter())
    artifact = orchestrator.propose_plan().model_copy(update={"provider": "other"})

    with pytest.raises(ApprovalRequiredError, match="different provider"):
        orchestrator.execute_approved_plan(
            artifact,
            approved=True,
            approved_by="test-analyst",
            disposition=RecommendedDisposition.CONTINUE,
            decision_note="Provider binding is required.",
        )


def test_plan_schema_avoids_unsupported_union_keyword() -> None:
    assert "oneOf" not in InvestigationPlan.model_json_schema()
    assert "oneOf" not in InvestigationAnalysis.model_json_schema()


def test_call_arguments_must_match_operation() -> None:
    with pytest.raises(ValidationError, match="arguments do not match"):
        PlannedEvidenceCall(
            call_id="call-0001",
            purpose="Invalid mixed tool arguments.",
            operation=EvidenceOperation.GET_RESOURCE_CONTEXT,
            evidence_ids=("ev-0001",),
            resource_id="instance-demo-017",
        )
