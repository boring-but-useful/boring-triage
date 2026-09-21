import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _canonical_pin(requirement: str) -> str:
    name, separator, version = requirement.partition("==")
    assert separator, f"Dependency must use an exact pin: {requirement}"
    normalized_name = re.sub(r"[-_.]+", "-", name).lower()
    return f"{normalized_name}=={version}"


def test_direct_dependency_pins_exist_in_lock_file() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = {
        _canonical_pin(requirement)
        for requirement in (
            *project["project"]["dependencies"],
            *project["project"]["optional-dependencies"]["dev"],
        )
    }
    locked = {
        _canonical_pin(line.strip())
        for line in (ROOT / "requirements-dev.lock")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.startswith("#")
    }

    assert declared <= locked
