"""Bounded local persistence for operator-reviewed workflow artifacts."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from pydantic import ValidationError

from boring_triage.errors import ArtifactError
from boring_triage.investigation import PlanArtifact

MAX_PLAN_BYTES = 256_000


def load_plan(path: str | Path) -> PlanArtifact:
    candidate = Path(path)
    if candidate.is_symlink():
        raise ArtifactError("plan artifact must not be a symbolic link")
    try:
        if not candidate.is_file():
            raise ArtifactError("plan artifact is not a regular file")
        if candidate.stat().st_size > MAX_PLAN_BYTES:
            raise ArtifactError("plan artifact exceeds the size limit")
        content = candidate.read_text(encoding="utf-8")
        return PlanArtifact.model_validate_json(content)
    except ArtifactError:
        raise
    except ValidationError as error:
        raise ArtifactError("plan artifact failed validation") from error
    except (OSError, UnicodeError) as error:
        raise ArtifactError("plan artifact could not be read") from error


def write_artifact(path: str | Path, content: str) -> None:
    """Atomically replace a regular local artifact without following a target link."""

    destination = Path(path)
    if destination.is_symlink():
        raise ArtifactError("artifact target must not be a symbolic link")
    parent = destination.parent
    if not parent.is_dir():
        raise ArtifactError("artifact parent directory does not exist")

    temporary_name: str | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            os.chmod(temporary.name, 0o600)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        Path(temporary_name).replace(destination)
    except OSError as error:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
        raise ArtifactError("artifact could not be written") from error
