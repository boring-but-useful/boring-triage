"""Command-line interface for evidence review and human-gated investigation."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from boring_triage.artifacts import load_plan, write_artifact
from boring_triage.errors import BoringTriageError
from boring_triage.fixtures import load_case
from boring_triage.investigation import (
    InvestigationOrchestrator,
    ModelAdapter,
    ModelProvider,
    RecommendedDisposition,
)
from boring_triage.model import FakeModelAdapter, OpenAIModelAdapter
from boring_triage.reports import render_markdown
from boring_triage.tools import EvidenceService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a validated Boring Triage case"
    )
    parser.add_argument("--case", required=True, help="Trusted local case directory")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("overview", help="Print the validated case overview")
    subparsers.add_parser("timeline", help="Print the deterministic evidence timeline")
    plan = subparsers.add_parser("plan", help="Propose and save an investigation plan")
    plan.add_argument("--provider", choices=("fake", "openai"), default="fake")
    plan.add_argument("--model", default="gpt-6-astra")
    plan.add_argument("--output", required=True, help="Plan JSON output path")

    investigate = subparsers.add_parser(
        "investigate", help="Execute an explicitly approved saved plan"
    )
    investigate.add_argument("--plan", required=True, help="Reviewed plan JSON path")
    investigate.add_argument(
        "--approve-plan",
        action="store_true",
        help="Approve exactly the saved plan supplied with --plan",
    )
    investigate.add_argument("--approved-by", default="local-operator")
    investigate.add_argument(
        "--disposition",
        required=True,
        choices=tuple(item.value for item in RecommendedDisposition),
    )
    investigate.add_argument("--decision-note", required=True)
    investigate.add_argument("--output", required=True, help="Markdown report path")
    return parser


def _adapter(provider: str | ModelProvider, model: str) -> ModelAdapter:
    if ModelProvider(provider) == ModelProvider.FAKE:
        return FakeModelAdapter()
    return OpenAIModelAdapter(model=model)


def _run(args: argparse.Namespace) -> None:
    service = EvidenceService(load_case(args.case))
    if args.command == "overview":
        print(json.dumps(service.get_case_overview().model_dump(mode="json"), indent=2))
        return

    if args.command == "timeline":
        for entry in service.timeline():
            observed_at = entry.observed_at.isoformat()
            print(
                f"{observed_at}  {entry.evidence_id}  {entry.source_type.value:<18} "
                f"{entry.event_category.value:<23} {entry.summary}"
            )
        return

    if args.command == "plan":
        adapter = _adapter(args.provider, args.model)
        artifact = InvestigationOrchestrator(service, adapter).propose_plan()
        write_artifact(args.output, artifact.model_dump_json(indent=2) + "\n")
        print(f"saved proposed plan to {args.output}; review it before approval")
        return

    artifact = load_plan(args.plan)
    adapter = _adapter(artifact.provider, artifact.model)
    record = InvestigationOrchestrator(service, adapter).execute_approved_plan(
        artifact,
        approved=args.approve_plan,
        approved_by=args.approved_by,
        disposition=RecommendedDisposition(args.disposition),
        decision_note=args.decision_note,
    )
    write_artifact(args.output, render_markdown(record))
    print(f"saved investigation report to {args.output}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        _run(args)
    except BoringTriageError as error:
        print(f"error: {error}")
        return 2
    return 0
