#!/usr/bin/env python3
"""Lint a requirement doc (Markdown) produced by the requirements-from-sources skill.

Usage: python lint_requirements.py <requirements.md> [--pack context-pack.json] [--ready]

--pack   cross-check Source IDs against the Context Pack
--ready  enforce the Definition of Ready (also applied automatically when Status is "Ready for design")

Exit code 1 if any ERROR is found. Warnings do not fail the run.
"""
import json
import re
import sys
from pathlib import Path

EM_DASH = "\u2014"
FEATURE_H = ["Summary", "Background and problem", "Goals and non-goals", "Users and stakeholders",
             "Scope", "Functional requirements", "User stories", "User flows",
             "Edge cases and error states", "Non-functional requirements",
             "Dependencies and integrations", "Risks and assumptions", "Open questions",
             "Conflicts and resolutions", "Source register", "Change log"]
BUG_H = ["Summary", "Environment", "Steps to reproduce", "Expected behavior", "Actual behavior",
         "Impact and severity", "Evidence", "Fix requirements", "Verification and acceptance",
         "Edge cases and regression risks", "Dependencies", "Open questions",
         "Conflicts and resolutions", "Source register", "Change log"]
PRIORITIES = {"must", "should", "could", "won't", "wont"}
BASES = {"stated", "confirmed", "assumption (approved)"}
STATUSES = {"draft", "in review", "ready for design"}
PLACEHOLDER = re.compile(
    r"\b(TBD|TODO|FIXME|lorem ipsum)\b|\?\?\?|<(?!/?(br|b|i|code|em|strong|p|ul|li)\b)[^>\n]{2,40}>", re.I)


def split_sections(text):
    parts = re.split(r"(?m)^## ", text)
    return {p.split("\n", 1)[0].strip(): (p.split("\n", 1)[1] if "\n" in p else "") for p in parts[1:]}


def table_rows(section):
    rows, header = [], None
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            continue
        if header is None:
            header = [c.lower() for c in cells]
            continue
        rows.append(dict(zip(header, cells)))
    return header, rows


def header_value(text, name):
    m = re.search(rf"\*\*{name}:\*\*\s*(.+)", text)
    return m.group(1).strip() if m else ""


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    path = args[0]
    pack = None
    if "--pack" in args:
        pack = json.loads(Path(args[args.index("--pack") + 1]).read_text())
    ready_flag = "--ready" in args
    text = Path(path).read_text()
    errors, warnings = [], []

    doc_type = header_value(text, "Type").lower()
    if doc_type not in ("feature", "bug"):
        print("ERROR: missing '**Type:** Feature' or '**Type:** Bug' line")
        sys.exit(1)
    status = header_value(text, "Status").lower()
    if status not in STATUSES:
        errors.append("Status must be Draft, In review, or Ready for design")
    ready = ready_flag or status == "ready for design"
    sections = split_sections(text)

    for h in (FEATURE_H if doc_type == "feature" else BUG_H):
        if h not in sections:
            errors.append(f"missing section: ## {h}")

    if EM_DASH in text:
        errors.append("contains em dashes; use commas, colons, or parentheses")

    body = re.sub(r"```.*?```", "", text, flags=re.S)
    for line in body.splitlines():
        hit = PLACEHOLDER.search(line)
        if hit:
            errors.append(f"placeholder or unresolved text: '{hit.group(0)}' (move unknowns to Open questions)")
            break

    # Source register
    sr_header, srcs = table_rows(sections.get("Source register", ""))
    source_ids = [r.get("id", "") for r in srcs]
    if not srcs:
        errors.append("Source register has no rows")
    if len(source_ids) != len(set(source_ids)):
        errors.append("duplicate IDs in Source register")
    for sid in source_ids:
        if not re.fullmatch(r"S\d+", sid):
            errors.append(f"bad source ID '{sid}' (expected S1, S2, ...)")
    if sr_header and "locator" not in sr_header:
        warnings.append("Source register has no Locator column (humans cannot re-check sources)")
    elif any(not r.get("locator") for r in srcs):
        warnings.append("some Source register rows have an empty Locator")

    # Requirements
    req_name = "Functional requirements" if doc_type == "feature" else "Fix requirements"
    header, reqs = table_rows(sections.get(req_name, ""))
    need = ["id", "requirement", "priority", "acceptance criteria", "basis", "sources"]
    req_ids = []
    if not header or any(n not in header for n in need):
        errors.append(f"{req_name} table must have columns: ID | Requirement | Priority | Acceptance criteria | Basis | Sources")
    elif not reqs:
        errors.append(f"{req_name} table has no rows")
    else:
        for r in reqs:
            rid = r.get("id", "")
            req_ids.append(rid)
            if not re.fullmatch(r"FR-\d+", rid):
                errors.append(f"bad requirement ID '{rid}' (expected FR-1, FR-2, ...)")
            if not r.get("requirement"):
                errors.append(f"{rid}: empty requirement text")
            if r.get("priority", "").lower() not in PRIORITIES:
                errors.append(f"{rid}: priority must be Must, Should, Could, or Won't")
            if len(r.get("acceptance criteria", "")) < 10:
                errors.append(f"{rid}: missing acceptance criteria")
            basis = r.get("basis", "").lower()
            if basis not in BASES:
                errors.append(f"{rid}: basis must be Stated, Confirmed, or Assumption (approved)")
            refs = re.findall(r"S\d+", r.get("sources", ""))
            if not refs and basis != "assumption (approved)":
                errors.append(f"{rid}: no source IDs (every requirement must trace to a source)")
            for s in refs:
                if s not in source_ids:
                    errors.append(f"{rid}: source {s} not in Source register")
        if len(req_ids) != len(set(req_ids)):
            errors.append("duplicate requirement IDs")

    for s in set(re.findall(r"\bS\d+\b", body)):
        if source_ids and s not in source_ids:
            errors.append(f"reference to {s} but it is not in Source register")
    for s in source_ids:
        outside = re.sub(r"(?s)## Source register.*?(?=\n## |\Z)", "", body)
        if not re.search(rf"\b{s}\b", outside):
            warnings.append(f"source {s} is never referenced outside the register (used or irrelevant?)")

    # Open questions
    oq_sec = sections.get("Open questions", "").strip()
    oq_header, oqs = table_rows(oq_sec)
    oq_ids = {r.get("id", "") for r in oqs}
    if not oqs and "none" not in oq_sec.lower():
        errors.append("Open questions must be a table or the word None")
    if oqs:
        if "blocking" not in (oq_header or []):
            errors.append("Open questions table needs a Blocking column (Yes or No)")
        for r in oqs:
            qid = r.get("id", "?")
            for k in ("question", "why it matters", "owner", "status"):
                if not r.get(k):
                    errors.append(f"{qid}: open question missing '{k}'")
            if r.get("blocking", "").lower() not in ("yes", "no"):
                errors.append(f"{qid}: Blocking must be Yes or No")
            if r.get("status", "").lower() not in ("open", "answered", "closed"):
                errors.append(f"{qid}: Status must be Open, Answered, or Closed")
    for ref in set(re.findall(r"\bOQ-\d+\b", body)):
        if ref not in oq_ids:
            errors.append(f"reference to {ref} but it is not in Open questions")

    # Conflicts
    c_sec = sections.get("Conflicts and resolutions", "").strip()
    _, conflicts = table_rows(c_sec)
    if not conflicts and "none" not in c_sec.lower():
        errors.append("Conflicts and resolutions must be a table or the word None")
    for c in conflicts:
        if c.get("status", "").lower() not in ("resolved", "pending"):
            errors.append(f"{c.get('id', '?')}: conflict Status must be Resolved or Pending")

    # Stories
    if doc_type == "feature":
        _, stories = table_rows(sections.get("User stories", ""))
        covered = set()
        for r in stories:
            for fr in re.findall(r"FR-\d+", r.get("requirements", "")):
                covered.add(fr)
                if fr not in req_ids:
                    errors.append(f"{r.get('id', '?')}: references {fr} which does not exist")
        for rid in req_ids:
            if rid not in covered:
                warnings.append(f"{rid} is not covered by any user story")

    # Context Pack cross-check
    if pack is not None:
        pack_ids = {i.get("id") for i in pack.get("items", [])}
        for s in source_ids:
            if s not in pack_ids:
                errors.append(f"{s} is in the Source register but not in the Context Pack")
        for s in sorted(pack_ids - set(source_ids)):
            warnings.append(f"Context Pack item {s} is not in the Source register (unused evidence?)")
        if pack.get("type") and pack["type"] != doc_type:
            errors.append(f"Context Pack type '{pack['type']}' does not match doc type '{doc_type}'")

    # Definition of Ready
    if ready:
        for r in oqs:
            if r.get("blocking", "").lower() == "yes" and r.get("status", "").lower() == "open":
                errors.append(f"not ready: {r.get('id')} is a blocking open question")
        for c in conflicts:
            if c.get("status", "").lower() == "pending":
                errors.append(f"not ready: conflict {c.get('id')} is unresolved")
        if status != "ready for design" and not errors:
            warnings.append("Definition of Ready met; Status may be set to 'Ready for design'")

    print(f"Type: {doc_type} | status: {status} | requirements: {len(req_ids)} | sources: {len(source_ids)} | open questions: {len(oqs)}")
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print("PASS" if not errors else f"FAIL: {len(errors)} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
