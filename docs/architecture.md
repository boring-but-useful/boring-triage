# Architecture

## Current Evidence Core

The implemented system is intentionally file-based and offline:

```text
trusted case-directory argument
            |
            v
     fixture loader
  containment + size checks
            |
            v
 strict Pydantic validation
 manifest + evidence + resources
            |
            v
      cross-validation
 IDs + case window + references
            |
            v
       EvidenceService
 bounded, case-scoped, read-only
            |
      +-----+------+---------+
      |            |         |
   overview      search    record/resource lookup
      |            |         |
      +------------+---------+
                   |
                   v
          deterministic CLI timeline
```

The command-line caller supplies a case directory. The fixture manifest may name only local JSON files. The loader rejects symbolic-link files, traversal, missing or oversized inputs, malformed models, mismatched case IDs, timestamps outside the case window, duplicate identifiers, and references to resources outside the bundle.

`EvidenceService` receives an already validated immutable `CaseBundle`. It cannot open files or reach a network. Searches use a fixed `EvidenceSearch` model rather than a query language and enforce the case's result limits and time window.

## Module Responsibilities

| Module | Responsibility | Explicitly does not do |
| --- | --- | --- |
| `domain.py` | Define immutable validated case, evidence, resource, search, overview, and timeline models | Load files, call providers, or infer incident meaning |
| `fixtures.py` | Resolve trusted fixture files and cross-validate the complete bundle | Accept paths from evidence or future model output |
| `tools.py` | Provide four bounded read-only operations over one bundle | Execute free-form queries, mutate evidence, or change case state |
| `cli.py` | Demonstrate validated overview and deterministic timeline output | Perform investigation or make a disposition |
| `errors.py` | Provide stable expected error categories | Expose raw fixture content in error messages |

## Data Flow And Trust

The directory argument is a local operator input. File contents are untrusted even when committed to the repository. Validation changes their state from unparsed input to structurally valid evidence; it does not make their claims true or their embedded text trustworthy.

`EvidenceService` owns a deep copy of the validated bundle and returns deep copies from record and resource lookups. This prevents a caller holding either the original bundle or a prior result from mutating later query results. The service returns validated records rather than synthesized evidence, preserving stable IDs for later citation validation.

## Planned Human/AI Boundary

The next slice will place an investigation orchestrator between a model adapter and `EvidenceService`:

```text
human -> investigation orchestrator -> model adapter
  |                |
  |                +-> validates proposed plan and structured output
  |                +-> records approvals and tool-call ledger
  |                +-> calls EvidenceService only after approval
  +-------------------> owns final disposition
```

The model adapter will not receive a filesystem path, shell, SQL interface, arbitrary HTTP client, or state-transition method. A fake adapter will exercise the complete flow offline before a live provider is introduced.

## Design Choices

- **JSON fixtures:** avoid another parser dependency in the evidence core.
- **No database:** one immutable case does not yet need persistence or concurrent access.
- **No generic repository interface:** there is only one concrete evidence source.
- **No MCP façade yet:** ordinary Python calls keep the enforcement boundary visible while tool contracts are still evolving.
- **No web framework yet:** the CLI proves the domain behavior before UI concerns are introduced.

These are current scope choices, not claims that the technologies are inherently inappropriate.
