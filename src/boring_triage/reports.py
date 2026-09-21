"""Human-readable investigation report rendering."""

from __future__ import annotations

from boring_triage.investigation import InvestigationRecord


def render_markdown(record: InvestigationRecord) -> str:
    lines = [
        f"# Investigation Report: {record.case_id}",
        "",
        "## Provenance",
        "",
        f"- Provider: `{record.provider}`",
        f"- Model: `{record.model}`",
        f"- Plan approved by: {record.approved_by}",
        f"- Plan approved at: {record.approved_at.isoformat()}",
        "",
        "## Approved Plan",
        "",
        record.plan.rationale,
        "",
    ]
    for call in record.plan.calls:
        lines.append(f"- `{call.call_id}` `{call.operation}`: {call.purpose}")

    lines.extend(["", "## Observed Facts", ""])
    for fact in record.analysis.facts:
        citations = ", ".join(f"`{item}`" for item in fact.evidence_ids)
        lines.append(f"- {fact.statement} Evidence: {citations}.")

    lines.extend(["", "## Hypotheses", ""])
    for hypothesis in record.analysis.hypotheses:
        citations = ", ".join(f"`{item}`" for item in hypothesis.evidence_ids)
        lines.append(
            f"- **{hypothesis.confidence.value} confidence:** "
            f"{hypothesis.statement} Evidence: {citations}."
        )

    lines.extend(["", "## Unknowns", ""])
    lines.extend(f"- {unknown}" for unknown in record.analysis.unknowns)

    recommendation = record.analysis.recommendation
    recommendation_citations = ", ".join(
        f"`{item}`" for item in recommendation.evidence_ids
    )
    lines.extend(
        [
            "",
            "## AI Recommendation",
            "",
            f"- Recommended disposition: `{recommendation.disposition.value}`",
            f"- Rationale: {recommendation.rationale}",
            f"- Evidence: {recommendation_citations}",
            "",
            "## Human Decision",
            "",
            f"- Final disposition: `{record.human_decision.disposition.value}`",
            f"- Decided by: {record.human_decision.decided_by}",
            f"- Decided at: {record.human_decision.decided_at.isoformat()}",
            f"- Note: {record.human_decision.note}",
            "",
        ]
    )
    return "\n".join(lines)
