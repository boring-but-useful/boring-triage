# Optional Model Setup

The project works completely offline with `--provider fake`. A live OpenAI request is optional and should use only the repository's synthetic case data.

An OpenAI API account needs its own API credits. A ChatGPT subscription does not supply API credit. If the CLI reports insufficient quota or credits, add API credit in [OpenAI billing settings](https://platform.openai.com/settings/organization/billing/) or continue using the offline adapter.

## Credential Setup

1. Create a project-scoped API key through the provider's secure key flow.
2. Copy `.env.example` to `.env.local` in the repository root.
3. Add the key as `OPENAI_API_KEY`. Do not put it in a command, screenshot, note, issue, commit, or chat message.
4. Restrict the local file and verify only its metadata:

   ```bash
   chmod 600 .env.local
   test -s .env.local && echo "credential file is non-empty"
   git check-ignore .env.local
   ```

The repository ignores `.env.local` and other `.env.*` files while allowing the empty `.env.example` template. The adapter reads only `OPENAI_API_KEY`; it does not import unrelated values into the process environment or log the credential.

If a key is accidentally exposed, revoke it in the provider console and create a replacement. Do not try to hide the exposure by only deleting a commit or terminal line.

## Live Workflow

Generate a structured plan:

```bash
.venv/bin/python -m boring_triage \
  --case fixtures/case-egress-001 \
  plan --provider openai --model gpt-6-astra \
  --output /tmp/boring-triage-live-plan.json
```

Inspect the saved JSON. The provider has proposed a plan but nothing in the plan has run. If the operation list and arguments are acceptable, execute that exact artifact with the approval command shown in the README.

The application, rather than the prompt, enforces the important boundaries:

- only schema-valid, case-scoped operations can appear in a plan;
- evidence operations do not run until `--approve-plan` is supplied;
- the plan is bound to its case, provider, and model;
- only records returned by the approved plan may be cited;
- AI recommendation and human disposition remain separate fields;
- no model-facing shell, filesystem, cloud, arbitrary HTTP, or remediation tool exists.

Provider requests disable response storage with `store=False`. Provider-side account and retention settings remain the operator's responsibility.

## References

- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [OpenAI API key safety](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)
