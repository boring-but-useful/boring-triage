# Boring Triage

Boring Triage is an early-stage, local-first incident-review project. Its goal is to demonstrate how a human and an AI assistant can investigate bounded cloud-security evidence without confusing model output with fact or giving the model autonomous response authority.

The current evidence-core slice is deliberately offline. It validates one synthetic AWS incident bundle, exposes four case-scoped read-only evidence operations, and prints a deterministic timeline. It does not yet call a model, provide a web interface, or connect to AWS.

## Current Capabilities

- Strict Pydantic validation for case manifests, evidence records, and resource context.
- One entirely synthetic unexpected-egress case using documentation-only IP ranges and fictional resource identifiers.
- Structured searches by source, time, resource, address, and event category.
- Bounded record retrieval and case-scoped resource lookup.
- Deterministic CLI overview and timeline.
- Negative tests for malformed fixtures, traversal attempts, broken IDs, invalid windows, excessive result requests, and instruction-like evidence remaining inert.
- Offline verification covering Ruff formatting/linting, strict mypy checks, pytest, and CLI smoke tests.

## Trust Boundary

All fixture content is untrusted data. A record can contain text that looks like an instruction, but the evidence layer only validates, filters, returns, and displays that text. It does not interpret it as a command.

The project currently has no shell, arbitrary-file, SQL, external-network, cloud-write, remediation, or case-closing capability.

## Local Setup

Python 3.12 or newer is required.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-deps -e .
make verify
```

`requirements-dev.lock` records the complete environment used for local verification. The direct application and development dependencies are also pinned in `pyproject.toml` so dependency automation can identify them later.

The vulnerability audit queries current advisory data and therefore requires network access:

```bash
make audit
```

## Demo

```bash
make demo
```

Or run the commands separately:

```bash
.venv/bin/python -m boring_triage --case fixtures/case-egress-001 overview
.venv/bin/python -m boring_triage --case fixtures/case-egress-001 timeline
```

## Evidence Operations

The core implements four operations:

1. `get_case_overview`
2. `search_evidence`
3. `get_evidence_records`
4. `get_resource_context`

They are ordinary Python methods for now. A model adapter or MCP interface will be considered only after the evidence boundary is stable.

## Deliberate Limits

- Synthetic fixtures only.
- One case.
- No live model or cloud credentials.
- No claim that an accepted flow-log record identifies the initiating process.
- No autonomous remediation or disposition.

The next slice will add a single human/AI investigation flow with structured output and an explicit plan-approval boundary.

## Design Documentation

- [Architecture](docs/architecture.md)
- [Threat Model](docs/threat_model.md)

## License

MIT
