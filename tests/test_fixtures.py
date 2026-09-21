from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from boring_triage.errors import FixtureError
from boring_triage.fixtures import load_case

CASE_DIRECTORY = Path(__file__).parents[1] / "fixtures" / "case-egress-001"


def _case_copy(tmp_path: Path) -> Path:
    destination = tmp_path / "case"
    shutil.copytree(CASE_DIRECTORY, destination)
    return destination


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_loads_valid_synthetic_case() -> None:
    bundle = load_case(CASE_DIRECTORY)

    assert bundle.manifest.case_id == "case-egress-001"
    assert len(bundle.evidence) == 11
    assert len(bundle.resources) == 7
    assert all(record.trust.value == "untrusted_input" for record in bundle.evidence)


def test_rejects_undeclared_evidence_fields(tmp_path: Path) -> None:
    case_directory = _case_copy(tmp_path)
    evidence_path = case_directory / "evidence.json"
    evidence = _read_json(evidence_path)
    evidence["records"][0]["unexpected"] = "not allowed"  # type: ignore[index]
    _write_json(evidence_path, evidence)

    with pytest.raises(FixtureError, match="evidence failed validation"):
        load_case(case_directory)


def test_rejects_manifest_path_traversal(tmp_path: Path) -> None:
    case_directory = _case_copy(tmp_path)
    manifest_path = case_directory / "manifest.json"
    manifest = _read_json(manifest_path)
    manifest["evidence_file"] = "../evidence.json"
    _write_json(manifest_path, manifest)

    with pytest.raises(FixtureError, match="manifest failed validation"):
        load_case(case_directory)


def test_rejects_duplicate_evidence_ids(tmp_path: Path) -> None:
    case_directory = _case_copy(tmp_path)
    evidence_path = case_directory / "evidence.json"
    evidence = _read_json(evidence_path)
    evidence["records"][1]["evidence_id"] = "ev-0001"  # type: ignore[index]
    _write_json(evidence_path, evidence)

    with pytest.raises(FixtureError, match="evidence IDs must be unique"):
        load_case(case_directory)


def test_rejects_unknown_resource_reference(tmp_path: Path) -> None:
    case_directory = _case_copy(tmp_path)
    evidence_path = case_directory / "evidence.json"
    evidence = _read_json(evidence_path)
    evidence["records"][0]["resource_ids"] = ["instance-not-in-case"]  # type: ignore[index]
    _write_json(evidence_path, evidence)

    with pytest.raises(FixtureError, match="references unknown resources: ev-0001"):
        load_case(case_directory)


def test_rejects_evidence_outside_case_window(tmp_path: Path) -> None:
    case_directory = _case_copy(tmp_path)
    evidence_path = case_directory / "evidence.json"
    evidence = _read_json(evidence_path)
    evidence["records"][0]["observed_at"] = "2026-09-21T15:00:00Z"  # type: ignore[index]
    _write_json(evidence_path, evidence)

    with pytest.raises(FixtureError, match="outside the case window: ev-0001"):
        load_case(case_directory)


def test_rejects_oversized_untrusted_attribute(tmp_path: Path) -> None:
    case_directory = _case_copy(tmp_path)
    evidence_path = case_directory / "evidence.json"
    evidence = _read_json(evidence_path)
    evidence["records"][0]["attributes"]["oversized"] = "x" * 1_001  # type: ignore[index]
    _write_json(evidence_path, evidence)

    with pytest.raises(FixtureError, match="evidence failed validation"):
        load_case(case_directory)
