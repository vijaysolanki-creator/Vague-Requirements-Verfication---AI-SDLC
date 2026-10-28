# Requirement doc template (full detail)

No em dashes. No placeholders such as TBD or TODO: unknowns go in Open questions. Every requirement row needs priority, acceptance criteria, basis, and sources. The linter checks the exact headings and table headers below.

- Status values: `Draft`, `In review`, `Ready for design`.
- Basis values: `Stated`, `Confirmed`, `Assumption (approved)`.
- Priority values: `Must`, `Should`, `Could`, `Won't`.
- Acceptance criteria: Given / When / Then, testable (use `<br>` for multiple lines in a cell).
- Source IDs `S1`, `S2`, ... are the Context Pack item IDs, listed in the Source register.
- Blocking column in Open questions: `Yes` or `No`. Open questions with `Yes` must be resolved before `Ready for design`.
- Open question Status values: `Open`, `Answered`, `Closed`.
- Conflict Status values: `Resolved`, `Pending`.

---

## FEATURE variant

```markdown
# <Feature name>: Requirements

**Type:** Feature
**Status:** Draft
**Version:** 0.1
**Date:** <date>
**Requested by:** <name or role from sources>
**Owner:** <name, or "Not stated (see OQ-n)">

## Summary
Three to five lines: what is being built, for whom, why now.

## Background and problem
Context, current behavior, pain, evidence. Cite sources (S1, S3).

## Goals and non-goals
**Goals** (with measurable success metrics where stated)
- <goal> (S1)

**Non-goals**
- <explicitly out of scope> (S2)

## Users and stakeholders
| Role | Needs | Source |
|---|---|---|
| <role> | <need> | S1 |

## Scope
**In scope:** bullets. **Out of scope:** bullets.

## Functional requirements
| ID | Requirement | Priority | Acceptance criteria | Basis | Sources |
|---|---|---|---|---|---|
| FR-1 | The system shall ... | Must | Given ..., when ..., then ... | Stated | S1, S3 |

## User stories
| ID | Story | Requirements |
|---|---|---|
| US-1 | As a <role>, I want <capability> so that <benefit>. | FR-1, FR-2 |

## User flows
Main flow as numbered steps. Alternate and error flows each as numbered steps. Use a Mermaid diagram when it helps.

## Edge cases and error states
| ID | Situation | Expected behavior | Basis | Sources |
|---|---|---|---|---|
| EC-1 | <situation> | <behavior> | Stated | S2 |

## Non-functional requirements
| Area | Requirement | Basis | Sources |
|---|---|---|---|
| Performance | <target> | Stated | S4 |
| Security | <rule> | Stated | S4 |
Cover: performance, security, privacy, accessibility, compliance, scalability, reliability, observability. If an area is not specified, write `Not specified, see OQ-n` in the Requirement cell and put `None` in Basis and Sources.

## Dependencies and integrations
Systems, teams, APIs, data, third parties, and their status.

## Risks and assumptions
| ID | Type | Description | Impact | Mitigation or status |
|---|---|---|---|---|
| R-1 | Risk | <risk> | <impact> | <mitigation> |
| A-1 | Assumption | <approved assumption> | <impact> | Approved by <user> on <date> |

## Open questions
| ID | Question | Why it matters | Blocking | Suggested default | Owner | Status |
|---|---|---|---|---|---|---|
| OQ-1 | <question> | <impact on scope or behavior> | Yes | <default or "None"> | <person or role> | Open |
Write `None` instead of the table if there are no open questions.

## Conflicts and resolutions
| ID | Conflict | Sources | Resolution | Decided by | Status |
|---|---|---|---|---|---|
| C-1 | <A vs B> | S2, S5 | <chosen> | <user> | Resolved |
Write `None` if there were no conflicts.

## Source register
| ID | Type | Author or origin | Date | Reliability | Locator | Summary |
|---|---|---|---|---|---|---|
| S1 | Email | <name, role> | <date> | High | <link, path, or message ID> | <one line> |

## Change log
| Version | Date | Change |
|---|---|---|
| 0.1 | <date> | Initial draft |
```

---

## BUG variant

```markdown
# <Bug title>: Requirements

**Type:** Bug
**Status:** Draft
**Version:** 0.1
**Date:** <date>
**Reported by:** <name or role>
**Owner:** <name, or "Not stated (see OQ-n)">

## Summary
Two to three lines: what is broken, who is affected, how bad.

## Environment
| Field | Value | Sources |
|---|---|---|
| App version | <value> | S1 |
| Platform and browser | <value> | S1 |
| Account or data conditions | <value> | S2 |

## Steps to reproduce
1. <step> (S1)

## Expected behavior
<what should happen> (S1)

## Actual behavior
<what happens> (S1)

## Impact and severity
Users affected, frequency, first seen, business impact, workaround, and a severity rating with the reason (S3).

## Evidence
Screenshots, logs, and messages with transcription notes (S2, S4). State what is not visible.

## Fix requirements
| ID | Requirement | Priority | Acceptance criteria | Basis | Sources |
|---|---|---|---|---|---|
| FR-1 | The system shall ... | Must | Given ..., when ..., then ... | Stated | S1 |

## Verification and acceptance
How to confirm the fix: test steps, data, environments, and who signs off.

## Edge cases and regression risks
| ID | Situation | Expected behavior | Basis | Sources |
|---|---|---|---|---|
| EC-1 | <related scenario to retest> | <behavior> | Stated | S2 |

## Dependencies
Teams, releases, hotfix constraints, related tickets.

## Open questions
(same table as feature)

## Conflicts and resolutions
(same table as feature)

## Source register
(same table as feature)

## Change log
(same table as feature)
```
