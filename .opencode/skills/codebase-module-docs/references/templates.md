# Templates

Use the same shape for every doc. If a section does not apply, write `None`. No em dashes.

## Module doc: `modules/<slug>.md`

```markdown
# <Module or feature name>

| Field | Value |
|---|---|
| Layer | frontend / backend / shared / full-stack |
| Path(s) | <main folders> |
| Files covered | <n> |

## Purpose
Two or three sentences: what this module is for and who or what uses it.

## Features
- <capability a user or another module gets, one bullet each>

## Files
| File | Layer | Role |
|---|---|---|
| `src/auth/login.ts` | backend | <one line: what it does and why it exists> |
| `src/ui/LoginForm.tsx` | frontend | <one line> |

## Dependencies
- **Internal modules used:** <list>
- **Used by:** <list>
- **External packages and services:** <list with why>
- **Env vars and config:** <list>

## Data flow
Numbered list (or Mermaid diagram) of the main flow: entry point, processing, storage or output. Include inputs, outputs, and side effects (DB, network, files, state). For backend note endpoints (method and path), models, and auth. For frontend note routes or screens, state, and API calls.

## Keywords
- `TermOrIdentifier`: <short meaning>
(domain terms, key functions, routes, events, config keys)

## Risks and gaps
Dead code, missing validation, tight coupling, `Unclear from code: ...`. Write `None` if empty.
```

## architecture.md outline

1. System summary (3 to 5 lines)
2. Layer map (frontend, backend, shared, infra) as a table
3. Module map: module, purpose, link to its doc
4. Module dependency diagram (Mermaid `graph TD`)
5. Key flows across modules (for example login, main create/read flow)
6. External systems and integrations
7. Cross-cutting concerns: auth, errors, logging, config
8. Known risks and gaps

## glossary.md outline

Alphabetical table: `Term | Meaning | Module doc`.

## README.md outline

Title, one-paragraph summary, links to `architecture.md`, `glossary.md`, `_coverage.md`, and a table of modules linking each doc.
