# Boring Triage

Boring Triage is a local-first incident-review project. It demonstrates how a human and an AI assistant can investigate bounded cloud-security evidence without confusing model output with fact or giving the model autonomous response authority.

The current vertical slice validates one synthetic AWS incident bundle, lets either a deterministic fake adapter or an optional OpenAI adapter propose a typed investigation plan, requires explicit human approval of the saved plan, executes only case-scoped read-only operations, validates every cited evidence ID, and records the AI recommendation separately from the human decision. It does not connect to AWS or provide remediation tools.

## Current Capabilities

- Strict Pydantic validation for case manifests, evidence records, and resource context.
- One entirely synthetic unexpected-egress case using documentation-only IP ranges and fictional resource identifiers.
- Structured searches by source, time, resource, address, and event category.
- Bounded record retrieval and case-scoped resource lookup.
- Deterministic CLI overview and timeline.
- Typed investigation plans and analyses with bounded fields and operations.
- A reviewable plan artifact that must be explicitly approved before execution.
- Application-enforced citation validation and separate AI/human dispositions.
- Deterministic offline adapter plus an optional live OpenAI adapter.
- Negative tests for malformed fixtures, traversal attempts, broken IDs, invalid windows, excessive result requests, and instruction-like evidence remaining inert.
- Offline verification covering Ruff formatting/linting, strict mypy checks, pytest, and CLI smoke tests.

## Trust Boundary

All fixture content is untrusted data. A record can contain text that looks like an instruction, but the evidence layer only validates, filters, returns, and displays that text. It does not interpret it as a command.

The model receives no shell, filesystem, SQL, arbitrary-network, cloud-write, remediation, or case-state tool. The optional provider adapter can only submit bounded structured requests to OpenAI. Final disposition remains a human-owned record.

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

The complete human-gated flow works offline. First save a proposed plan:

```bash
.venv/bin/python -m boring_triage \
  --case fixtures/case-egress-001 \
  plan --provider fake --output /tmp/boring-triage-plan.json
```

Read the JSON plan. If it is acceptable, explicitly approve that exact artifact and record a human decision:

```bash
.venv/bin/python -m boring_triage \
  --case fixtures/case-egress-001 \
  investigate \
  --plan /tmp/boring-triage-plan.json \
  --approve-plan \
  --approved-by local-analyst \
  --disposition continue_investigation \
  --decision-note "Collect process telemetry before closure." \
  --output /tmp/boring-triage-report.md
```

Omitting `--approve-plan` fails closed before evidence operations or analysis occur.

## Optional Live Model

Copy `.env.example` to `.env.local`, add an API key, and keep the file local. The CLI reads only `OPENAI_API_KEY` from that file and never prints it. Then replace `--provider fake` in the planning command with `--provider openai`. The saved artifact binds the provider and model used for both stages.

Only synthetic, public-safe case data should be sent to a model provider. See [Model Setup](docs/model_setup.md) for the credential and live-run process.

## Evidence Operations

The core implements four operations:

1. `get_case_overview`
2. `search_evidence`
3. `get_evidence_records`
4. `get_resource_context`

They remain ordinary Python methods behind the orchestrator. The model proposes typed calls; application code validates and executes them only after approval. The model does not receive executable tools directly.

## Deliberate Limits

- Synthetic fixtures only.
- One case.
- Live model use is optional; cloud credentials are not supported.
- No claim that an accepted flow-log record identifies the initiating process.
- No autonomous remediation or disposition.

- No claim that a valid citation necessarily supports the sentence that cites it; semantic citation evaluation remains future work.
- No web interface, persistent database, multi-user authorization, or production retention controls.

## Design Documentation

- [Architecture](docs/architecture.md)
- [Threat Model](docs/threat_model.md)
- [Model Setup](docs/model_setup.md)

## License

MIT
