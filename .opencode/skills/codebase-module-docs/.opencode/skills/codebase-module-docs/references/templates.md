# Templates

Use these exactly. Omit a section only if it truly does not apply, and then write `None` rather than deleting it, so every doc has the same shape.

No em dashes in any generated doc.

## File doc template

Path: `<output>/<module>/files/<relative_path>.md`

```markdown
# <relative/path/to/file.ext>

| Field | Value |
|---|---|
| Module | <module> |
| Layer | frontend / backend / shared / config / test |
| Language | <language> |
| Lines | <n> |

## Purpose
One or two sentences: why this file exists.

## Responsibilities
- <what it owns, one bullet each>

## Features offered
- <capability a caller or end user gets from this file>

## Keywords
`TermOne`, `functionName`, `/api/route`, `ENV_VAR`, `EventName`
(One line each below if a term needs a meaning.)
- `TermOne`: <meaning>

## Dependencies
| Type | Name | Why |
|---|---|---|
| Internal | `../auth/session.ts` | <reason> |
| External | `express` | <reason> |
| Service | PostgreSQL | <reason> |
| Env var | `JWT_SECRET` | <reason> |

## Data flow
- **Inputs:** <args, request body, props, events, config>
- **Outputs:** <return values, responses, rendered UI, emitted events>
- **Side effects:** <DB writes, network calls, file IO, global state, logs>
- **Called by:** <files or routes that use this>

## Notes
Edge cases, risks, TODOs, or `Unclear from code: ...`. Write `None` if empty.
```

Frontend extras (add under Data flow): route or screen, props, local and global state, API calls made.

Backend extras (add under Data flow): endpoints exposed (method and path), models touched, auth and validation applied, jobs, queues, or events handled.

## Module overview template

Path: `<output>/<module>/overview.md`

```markdown
# Module: <module>

| Field | Value |
|---|---|
| Layer | frontend / backend / shared |
| Path | <module path> |
| Files documented | <n> |

## Purpose
What this module is for, in two or three sentences.

## Features
- <user or system capability, one bullet each>

## Structure
| File | Purpose | Doc |
|---|---|---|
| `src/a.ts` | <one line> | [link](files/src/a.ts.md) |

## Dependencies
- **Depends on (internal modules):** <list>
- **Used by (internal modules):** <list>
- **External packages and services:** <list>
- **Env vars and config:** <list>

## Data flow
Describe the main flow end to end (entry point, processing, storage or output). Use a numbered list or a Mermaid diagram.

## Keywords
Alphabetical list with a short meaning each.

## Risks and gaps
Dead code, missing validation, tight coupling, unclear areas. Write `None` if empty.
```

## architecture.md outline

1. System summary (3 to 5 lines)
2. Layer map (frontend, backend, shared, infra) as a table
3. Module map with one-line purpose each
4. Module dependency diagram (Mermaid `graph TD`)
5. Key flows (for example login, main create/read flow), each as a numbered list across modules
6. External systems and integrations
7. Cross-cutting concerns: auth, error handling, logging, config
8. Known risks and gaps

## glossary.md outline

Alphabetical table: `Term | Meaning | Where used (module or file)`.

## README.md outline

Title, one-paragraph summary, link to `architecture.md` and `glossary.md`, table of modules linking each `overview.md`, link to `_coverage.md`.
