---
name: jira-ticket-from-doc
description: Generate a Jira ticket (Summary, Description, Acceptance criteria) in a fixed team format from a document the user provides, such as a security advisory, incident report, change request, runbook, release note, design doc, or meeting notes. Use whenever the user asks to create, draft, write, or convert something into a Jira ticket, story, task, bug, or work item from a document, pasted text, or uploaded file, even if they do not say "Jira" explicitly (for example "turn this into a ticket" or "raise a task for this").
---

# Jira Ticket From Document

Turn a source document into a ready-to-paste Jira ticket in the team's fixed format.
Read `references/example-ticket.md` once before drafting. It is the gold standard for tone, density, and structure.

## Workflow

1. **Read the whole document.** Identify the single outcome the ticket delivers.
2. **Extract facts only from the document.** Never invent versions, CVE IDs, dates, owners, environments, or numbers. If a required fact is missing, write `TBD` and list it under "Open questions" after the ticket.
3. **Draft the ticket** using the template below.
4. **Self-check** against the checklist at the bottom.
5. **Output** the ticket in a single markdown code block so it can be pasted into Jira, followed by "Open questions" only if any exist.

## Output template

```
Summary
<Verb> <what> on <where> - <why / reference ID>

Description
Background
<2-4 sentences: what happened or was found, why it matters, what is exposed>

Current state (before)
* <Item>: <state> -> <impact>

Other items reviewed        (include only if the document reviews things that were ruled out)
* <Item> - <verdict and one-line reason>

Action taken                (use "Planned action" if the work is not done yet)
1. <Imperative step>
2. <Imperative step>

After                       (use "After (expected)" if not done yet)
* <Target state>

Out of scope
* <Explicit exclusion>

Acceptance criteria
* [ ] <Observable, verifiable condition>
```

## Rules

**Summary**
- One line, under 120 characters, starts with a verb (Upgrade, Fix, Migrate, Add, Remove, Rotate).
- Contains the target, the environment, and the driver (CVE, incident, or ticket ID) when one exists.

**Description**
- Keep section names and order exactly as in the template. Drop a section only if marked optional and not applicable. Never rename or add sections.
- Background answers: what, why now, and what is exposed. No history lessons.
- Current state and After must be parallel, so a reader can diff them at a glance.
- Wrap versions, commands, file paths, config keys, and code identifiers in backticks.
- Steps are imperative, ordered, and runnable by someone who has not read the source document.
- Out of scope lists what a reasonable reader might assume is included but is not.

**Acceptance criteria**
- Each item is binary (pass or fail) and states how it is verified (command, test, screenshot, log).
- Cover every environment named in the ticket separately.
- Include a negative criterion when the ticket promises something will not happen (for example "no redeploy required").
- Use Jira checkbox syntax `* [ ]`.

**Style**
- Concise and factual. No filler, no marketing words.
- Do not use em dashes or en dashes anywhere. Use a hyphen with spaces ( - ) or restructure the sentence.
- Do not output auto-link artifacts such as `[ASP.NET](http://ASP.NET)`. Write plain names.
- Use the document's own terminology for systems and environments.

## Multiple work items

If the document contains independent deliverables (different systems, owners, or release timing), produce one ticket per deliverable, each in its own code block, and add a one-line note on how you split them. If they share one outcome and one owner, keep them as a single ticket.

## Self-check before output

- [ ] Every fact traces back to the document or is marked `TBD`
- [ ] Summary is one line and starts with a verb
- [ ] Current state and After mirror each other
- [ ] Every acceptance criterion is verifiable
- [ ] Every environment has its own acceptance criterion
- [ ] No em dashes, no en dashes, no auto-link artifacts
