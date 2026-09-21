"""Load and cross-validate a synthetic case fixture from a trusted directory."""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from boring_triage.domain import (
    CaseBundle,
    CaseManifest,
    EvidenceFile,
    ResourceContextFile,
)
from boring_triage.errors import FixtureError

MAX_FIXTURE_BYTES = 2_000_000


def _validation_summary(label: str, error: ValidationError) -> str:
    locations = [".".join(str(part) for part in item["loc"]) for item in error.errors(include_input=False)]
    shown = ", ".join(locations[:5])
    suffix = "" if len(locations) <= 5 else ", ..."
    return f"{label} failed validation at: {shown}{suffix}"


def _read_fixture_file(root: Path, filename: str) -> str:
    candidate = root / filename
    if candidate.is_symlink():
        raise FixtureError(f"fixture file must not be a symbolic link: {filename}")

    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError) as error:
        raise FixtureError(f"fixture file is missing or outside the case directory: {filename}") from error

    if not resolved.is_file():
        raise FixtureError(f"fixture path is not a regular file: {filename}")
    if resolved.stat().st_size > MAX_FIXTURE_BYTES:
        raise FixtureError(f"fixture file exceeds {MAX_FIXTURE_BYTES} bytes: {filename}")

    try:
        return resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise FixtureError(f"fixture file could not be read as UTF-8: {filename}") from error


def _validate_bundle(bundle: CaseBundle) -> None:
    manifest = bundle.manifest
    evidence_ids = [record.evidence_id for record in bundle.evidence]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise FixtureError("evidence IDs must be unique within a case")

    resource_ids = [resource.resource_id for resource in bundle.resources]
    if len(resource_ids) != len(set(resource_ids)):
        raise FixtureError("resource IDs must be unique within a case")
    known_resources = set(resource_ids)

    for record in bundle.evidence:
        if record.case_id != manifest.case_id:
            raise FixtureError(f"evidence record has a mismatched case ID: {record.evidence_id}")
        if not manifest.start_time <= record.observed_at <= manifest.end_time:
            raise FixtureError(f"evidence record is outside the case window: {record.evidence_id}")
        unknown_resources = set(record.resource_ids) - known_resources
        if unknown_resources:
            raise FixtureError(f"evidence record references unknown resources: {record.evidence_id}")

    for resource in bundle.resources:
        if resource.case_id != manifest.case_id:
            raise FixtureError(f"resource has a mismatched case ID: {resource.resource_id}")
        if not manifest.start_time <= resource.observed_at <= manifest.end_time:
            raise FixtureError(f"resource context is outside the case window: {resource.resource_id}")


def load_case(case_directory: str | Path) -> CaseBundle:
    """Load one case without accepting fixture filenames from an AI or query caller."""

    supplied_root = Path(case_directory)
    if supplied_root.is_symlink():
        raise FixtureError("case directory must not be a symbolic link")
    try:
        root = supplied_root.resolve(strict=True)
    except FileNotFoundError as error:
        raise FixtureError("case directory does not exist") from error
    if not root.is_dir():
        raise FixtureError("case path is not a directory")

    try:
        manifest = CaseManifest.model_validate_json(_read_fixture_file(root, "manifest.json"))
    except ValidationError as error:
        raise FixtureError(_validation_summary("manifest", error)) from error

    try:
        evidence_file = EvidenceFile.model_validate_json(
            _read_fixture_file(root, manifest.evidence_file)
        )
    except ValidationError as error:
        raise FixtureError(_validation_summary("evidence", error)) from error

    try:
        resource_file = ResourceContextFile.model_validate_json(
            _read_fixture_file(root, manifest.resource_context_file)
        )
    except ValidationError as error:
        raise FixtureError(_validation_summary("resource context", error)) from error

    bundle = CaseBundle(
        manifest=manifest,
        evidence=evidence_file.records,
        resources=resource_file.resources,
    )
    _validate_bundle(bundle)
    return bundle
