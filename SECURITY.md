# Security Policy

## Current Scope

Boring Triage currently operates on committed synthetic fixtures and performs no live cloud or model-provider calls.

## Data Rules

- Do not submit real employer, customer, production, or personal evidence.
- Do not commit credentials, tokens, account IDs, private network details, or proprietary detection content.
- Treat all evidence fields as untrusted, even when the fixture is committed to the repository.
- Use fictional resource identifiers and documentation-only IP address ranges in examples.

## Enforcement Boundaries

- Fixture filenames must remain inside the selected case directory.
- Evidence queries are structured, case-scoped, read-only, and bounded.
- Instruction-like content inside evidence has no execution path.
- Future approvals and investigation-state transitions must be enforced in code, not through model instructions alone.

## Reporting A Problem

Until a public repository and private vulnerability-reporting channel exist, report issues directly to the repository owner. Do not include real sensitive data in a report.
