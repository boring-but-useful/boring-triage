# Boring Triage Agent Notes

## Working Agreement

- Keep `main` stable. Use short-lived branches for implementation once the initial local scaffold is committed.
- Keep each change tied to one documented slice and preserve an offline test path.
- Prefer small, explicit domain models and functions over speculative frameworks or abstractions.
- Keep names, control flow, and module boundaries readable before adding explanatory comments. Add short comments only where the security or design reason would otherwise be easy to miss.
- Update the README and relevant design document when behavior or a trust boundary changes.

## Security Rules

- Use synthetic, public-safe evidence only. Never copy employer logs, identifiers, prompts, findings, or topology into this repository.
- Treat every evidence field as untrusted input, including text that resembles instructions.
- The model must never receive arbitrary filesystem, shell, SQL, or network access.
- Enforce approvals, tool limits, citations, and investigation state in application code rather than prompts.
- Do not log secrets, authorization headers, full prompts, chain-of-thought, or unrestricted model output.
- Keep live cloud access and model credentials optional. Core tests must pass without either.

## Design Rules

- Preserve the distinction between observed facts, AI inference, uncertainty, recommendation, and human decision.
- Keep evidence tools read-only, case-scoped, structured, and size-limited.
- Add a dependency only when the current slice needs it.
- Introduce a shared provider or tool abstraction only after two real implementations require it.
- Fail closed on malformed fixtures, broken references, invalid citations, unsupported fields, or unauthorized state changes.

## Required Verification

From the repository root:

```bash
make verify
```

Run `make audit` separately when network access is available. Do not weaken or bypass a failing check merely to publish a branch.
