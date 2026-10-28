---
name: codebase-module-docs
description: Reads every source file in a codebase (frontend and backend) and produces detailed, structured documentation in one output folder, with a doc per file, an overview per module, an architecture doc, and a glossary of keywords. Use this skill whenever the user asks to document a codebase, repo, project, module, service, or app, wants onboarding or handover docs, asks "explain what every file does", wants a full code walkthrough, architecture write-up, or knowledge base from source code, even if they do not say "documentation" explicitly.
---

# Codebase Module Docs

Produce complete, accurate documentation for a codebase by reading every file, then synthesizing upward: file, module, system.

## Core principle

Reading everything in one pass will overflow context and produce shallow output. Work in layers and write to disk as you go, so progress survives and nothing is skipped.

| Layer | Output | Source of truth |
|---|---|---|
| 1. Inventory | `_manifest.json` | `scripts/inventory.py` |
| 2. File docs | one `.md` per source file | the file itself |
| 3. Module overview | `overview.md` per module | the file docs, not a re-read of code |
| 4. System | `architecture.md`, `glossary.md`, `README.md` | module overviews |
| 5. Verification | `_coverage.md` | `scripts/verify_coverage.py` |

## Rules

1. Never document a file you have not opened. Never invent behavior. If something is unclear, write `Unclear from code: <what>` instead of guessing.
2. Do not use em dashes anywhere in the generated docs. Use commas, colons, or parentheses.
3. Be concise and concrete. Prefer bullets and tables over prose. No filler.
4. Every non-skipped file gets a doc, including tiny ones (a short doc is fine).
5. Skipped files (lockfiles, binaries, build output, vendored code) must be listed with a reason in `_coverage.md`, never silently dropped.
6. Write each file doc immediately after reading the file. Do not batch docs in memory.

## Workflow

### Step 1: Scope (ask only if missing)

Confirm with the user, only if not already stated:
- Repo root path (default: current working directory or `/mnt/user-data/uploads`)
- Output folder (default: `docs/codebase`; when running in Claude.ai, write to `/mnt/user-data/outputs/codebase-docs`)
- Any directories to exclude beyond the defaults

If the repo is a zip or archive, extract it first.

### Step 2: Inventory

```bash
python scripts/inventory.py <repo_root> <output_folder>
```

This writes `<output_folder>/_manifest.json` and prints a summary: files per module, per layer (frontend, backend, shared, config, tests), and skipped files with reasons. Review the module grouping. If it is wrong (for example a monorepo grouped too coarsely), fix `module` values in the manifest before continuing.

Tell the user the file count and module list, and recommend the processing order: shared and backend core first, then backend features, then frontend. Dependencies are easier to document once their targets are known.

### Step 3: Document each file

Process one module at a time, in batches of roughly 10 to 15 files. For each file:

1. Open and read the full file (for files over 800 lines, read in chunks).
2. Write its doc to `<output_folder>/<module>/files/<relative_path>.md` using the template in `references/templates.md`.
3. Tick it off in `<output_folder>/_progress.md`.

Each file doc must cover:
- Purpose and responsibilities
- Features it offers (what a caller or user can do because this file exists)
- Keywords (domain terms, key identifiers, patterns, config keys, route paths, event names)
- Dependencies: internal imports, external packages, services, env vars
- Data flow: inputs, outputs, side effects (DB, network, files, state), and who calls it

For frontend files also note: route or screen it belongs to, props or state it owns, API calls it makes. For backend files also note: endpoints exposed, models touched, auth applied, jobs or events handled.

### Step 4: Module overview

After finishing a module, write `<output_folder>/<module>/overview.md` from the file docs (do not re-read the code unless a gap appears). Use the module template in `references/templates.md`. It must include a file index table linking every file doc, the module's features, internal and external dependencies, the end-to-end data flow, and a keyword list.

### Step 5: System docs

Write, from the module overviews:
- `architecture.md`: layers, module map, how frontend talks to backend, main request flows, external systems, and a Mermaid diagram of module dependencies.
- `glossary.md`: merged and de-duplicated keywords across modules, alphabetical, each with a one-line meaning and the module or file where it lives.
- `README.md`: index of everything with links, plus how to read the docs.

### Step 6: Verify

```bash
python scripts/verify_coverage.py <output_folder>
```

It checks that every non-skipped file in the manifest has a doc and writes `_coverage.md`. Fix every missing entry, then rerun until it reports 100 percent. Report the final numbers to the user.

## Context management

- If the repo has more than about 150 source files, work module by module and tell the user the plan up front. Finish and verify one module before starting the next.
- If the session is interrupted, resume from `_progress.md` and `verify_coverage.py` output. Never restart from scratch.
- Do not paste whole files into docs. Reference by path and line range when pointing at specific code.

## Final response to the user

Keep it short: output folder path, modules documented, file counts (documented, skipped), anything marked `Unclear from code`, and 2 to 3 risks or gaps noticed while reading (for example dead code, missing auth checks, circular dependencies). Offer next steps only if they are clearly useful.
