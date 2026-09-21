# Threat Model

## Scope

This document covers the offline evidence core and the planned human/AI investigation boundary. Version 1 uses synthetic data only and has no live AWS, model, ticketing, shell, or remediation access.

## Assets

- Integrity of the evidence bundle and its stable identifiers.
- Integrity of human approvals and final disposition.
- Separation between observed facts, AI inference, and human judgment.
- Model credentials and provider request data when a live adapter is added.
- Reliability of reports and evaluation results.

## Trust Boundaries

1. Local operator to case-directory loader.
2. Untrusted fixture bytes to validated domain models.
3. Validated evidence service to the future model context.
4. Future model output to application state and human-visible analysis.
5. Human approval to evidence-tool execution and final disposition.

Structural validation establishes format and references; it does not make a source statement trustworthy.

## Primary Threats And Current Controls

| Threat | Current control | Residual concern |
| --- | --- | --- |
| Path traversal through manifest filenames | Manifest accepts local `.json` basenames only; resolved files must remain under the case root | The operator can intentionally select any readable case directory; this is not a model capability |
| Symbolic-link escape | Case directory and referenced fixture files reject symbolic links | Platform-specific filesystem behavior needs CI coverage after publication |
| Resource exhaustion from fixtures | Two-megabyte file limit, bounded record/resource counts, bounded strings/lists, and bounded query results | Future model prompts need an additional context/token budget |
| Malformed or inconsistent evidence | Strict models, forbidden extra fields, aware timestamps, unique IDs, case-window checks, and resource-reference checks | Structurally valid evidence can still be false or misleading |
| Indirect prompt injection in evidence | Evidence is returned as immutable untrusted data; the current layer has no instruction execution or state-changing operation | A live model may still follow injected text; Slice 2 requires adversarial evaluation and application-enforced gates |
| Arbitrary query execution | Fixed search fields; no SQL, regex, expression language, shell, or filesystem parameters | Repeated small queries may still collect the whole case; this is acceptable for synthetic version 1 but should be logged |
| Evidence tampering after validation | Frozen Pydantic models; service-owned deep copy; deep-copied query results; no mutation operations | Python callers deliberately reaching private attributes remain outside this non-hostile, single-process boundary |
| Unsupported incident claims | Stable evidence IDs prepare for deterministic citation checks | Semantic support quality requires evaluation; a valid citation can still be irrelevant |
| Excessive AI agency | No model exists yet; planned tools are read-only and case-scoped | The future orchestrator must own state transitions and never rely on prompt obedience |
| Secret leakage | Synthetic fixtures, `.env` exclusions, bounded errors, and no credential requirement | Live-provider prompts, responses, and telemetry will require explicit redaction and retention decisions |

## Planned Controls Before A Live Model

- Explicit investigation state machine enforced outside the model.
- Structured plan and analysis schemas with size and enum limits.
- Human approval before executing the proposed evidence plan.
- Deterministic validation that cited evidence IDs exist.
- Separate storage for AI recommendations and human decisions.
- Tool-call ledger containing validated arguments, approvals, result IDs, duration, and outcome.
- Fake model adapter for complete offline behavior and failure testing.
- Adversarial evaluation proving the injected evidence string cannot close a case, expand tool access, or suppress a record.

## Out Of Scope

- Protection against malicious operating-system administrators.
- Multi-user authorization and tenant isolation.
- Production evidence retention and legal-hold requirements.
- Live cloud collection, containment, or remediation.
- Guarantees that a model will never generate an incorrect interpretation.

The project should state these limits directly rather than imply production assurance.
