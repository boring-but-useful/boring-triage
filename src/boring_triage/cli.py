"""Command-line demonstration for the offline evidence core."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from boring_triage.errors import BoringTriageError
from boring_triage.fixtures import load_case
from boring_triage.tools import EvidenceService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect a validated Boring Triage case")
    parser.add_argument("--case", required=True, help="Trusted local case directory")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("overview", help="Print the validated case overview")
    subparsers.add_parser("timeline", help="Print the deterministic evidence timeline")
    return parser


def _run(args: argparse.Namespace) -> None:
    service = EvidenceService(load_case(args.case))
    if args.command == "overview":
        print(json.dumps(service.get_case_overview().model_dump(mode="json"), indent=2))
        return

    for entry in service.timeline():
        observed_at = entry.observed_at.isoformat()
        print(
            f"{observed_at}  {entry.evidence_id}  {entry.source_type.value:<18} "
            f"{entry.event_category.value:<23} {entry.summary}"
        )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        _run(args)
    except BoringTriageError as error:
        print(f"error: {error}")
        return 2
    return 0
