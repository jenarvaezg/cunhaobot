# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This is a single-context repo.

- Read `CONTEXT.md` at the repo root before domain-sensitive work.
- Read `docs/domain-code-map.md` when translating domain terms into code changes.
- Read relevant ADRs under `docs/adr/` if that directory exists.
- If optional docs do not exist, proceed silently. Do not suggest creating them upfront.

The producer skill (`/grill-with-docs`) creates missing context or ADR files lazily when terms or decisions actually get resolved.

## File structure

```text
/
├── CONTEXT.md
├── docs/domain-code-map.md
├── docs/adr/
│   ├── 0001-example-decision.md
│   └── 0002-example-decision.md
└── src/
```

## Use the glossary's vocabulary

When your output names a domain concept in an issue title, refactor proposal, hypothesis, or test name, use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly avoids.

If the concept you need is not in the glossary yet, reconsider whether you are inventing language the project does not use. If it is a real gap, note it for `/grill-with-docs`.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding it.
