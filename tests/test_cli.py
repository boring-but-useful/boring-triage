from __future__ import annotations

from pathlib import Path

from boring_triage.cli import main

CASE_DIRECTORY = Path(__file__).parents[1] / "fixtures" / "case-egress-001"


def test_overview_command_prints_validated_case(capsys) -> None:  # type: ignore[no-untyped-def]
    result = main(["--case", str(CASE_DIRECTORY), "overview"])

    output = capsys.readouterr().out
    assert result == 0
    assert '"case_id": "case-egress-001"' in output
    assert '"evidence_count": 11' in output


def test_timeline_command_prints_evidence_in_order(capsys) -> None:  # type: ignore[no-untyped-def]
    result = main(["--case", str(CASE_DIRECTORY), "timeline"])

    output = capsys.readouterr().out
    assert result == 0
    assert output.index("ev-0001") < output.index("ev-0011")
    assert "203.0.113.42" not in output
