from __future__ import annotations

from pathlib import Path

import pytest

from boring_triage.artifacts import load_plan, write_artifact
from boring_triage.errors import ArtifactError
from boring_triage.fixtures import load_case
from boring_triage.investigation import InvestigationOrchestrator
from boring_triage.model import FakeModelAdapter
from boring_triage.tools import EvidenceService

CASE_DIRECTORY = Path(__file__).parents[1] / "fixtures" / "case-egress-001"


def _plan_json() -> str:
    service = EvidenceService(load_case(CASE_DIRECTORY))
    artifact = InvestigationOrchestrator(service, FakeModelAdapter()).propose_plan()
    return artifact.model_dump_json(indent=2)


def test_plan_artifact_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "plan.json"

    write_artifact(path, _plan_json())

    assert load_plan(path).case_id == "case-egress-001"
    assert path.stat().st_mode & 0o777 == 0o600


def test_plan_loader_rejects_symbolic_link(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text(_plan_json(), encoding="utf-8")
    link = tmp_path / "plan.json"
    link.symlink_to(target)

    with pytest.raises(ArtifactError, match="symbolic link"):
        load_plan(link)


def test_plan_loader_rejects_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "plan.json"
    path.write_text(
        _plan_json().replace('"provider": "fake"', '"extra": true,'), encoding="utf-8"
    )

    with pytest.raises(ArtifactError, match="validation"):
        load_plan(path)
