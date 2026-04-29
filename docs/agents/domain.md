# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This repo uses a **single-context** domain docs layout.

Expected locations:

- `CONTEXT.md` at the repo root for project glossary, business language, and domain boundaries
- `docs/adr/` for architectural decision records

## Before exploring, read these

- `CONTEXT.md` at the repo root, if it exists
- Relevant ADRs under `docs/adr/`, if they exist

If these files do not exist, proceed silently. Do not block the task and do not suggest creating them upfront.

## Use the glossary's vocabulary

When your output names a domain concept, use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly avoids.

If the concept you need is not in the glossary yet, note it only when it matters to the task.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding it.
