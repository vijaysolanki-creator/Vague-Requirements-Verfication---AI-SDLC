#!/usr/bin/env python3
"""Export a requirement doc (Markdown) to machine-readable JSON for downstream SDLC stages.

Usage: python export_requirements.py <requirements.md> <requirements.json>

Run lint_requirements.py first. The JSON schema id is "requirements/v1".
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_requirements import header_value, split_sections, table_rows  # noqa: E402


def key(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def rows(sections, name):
    _, rs = table_rows(sections.get(name, ""))
    return [{key(k): v for k, v in r.items()} for r in rs]


def ids(cell):
    return re.findall(r"S\d+", cell or "")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    text = Path(sys.argv[1]).read_text()
    sections = split_sections(text)
    doc_type = header_value(text, "Type").lower()
    title = re.search(r"(?m)^# (.+)", text)
    req_section = "Functional requirements" if doc_type == "feature" else "Fix requirements"

    requirements = []
    for r in rows(sections, req_section):
        r["sources"] = ids(r.get("sources"))
        r["acceptance_criteria"] = [a.strip() for a in re.split(r"<br\s*/?>", r.get("acceptance_criteria", "")) if a.strip()]
        requirements.append(r)

    open_q = rows(sections, "Open questions")
    conflicts = rows(sections, "Conflicts and resolutions")
    blocking_open = [q["id"] for q in open_q if q.get("blocking", "").lower() == "yes" and q.get("status", "").lower() == "open"]
    pending = [c["id"] for c in conflicts if c.get("status", "").lower() == "pending"]

    out = {
        "schema": "requirements/v1",
        "title": title.group(1).strip() if title else "",
        "type": doc_type,
        "status": header_value(text, "Status"),
        "version": header_value(text, "Version"),
        "date": header_value(text, "Date"),
        "ready_for_design": header_value(text, "Status").lower() == "ready for design" and not blocking_open and not pending,
        "blocking_open_questions": blocking_open,
        "pending_conflicts": pending,
        "requirements": requirements,
        "user_stories": rows(sections, "User stories") if doc_type == "feature" else [],
        "edge_cases": rows(sections, "Edge cases and error states" if doc_type == "feature" else "Edge cases and regression risks"),
        "non_functional": rows(sections, "Non-functional requirements") if doc_type == "feature" else [],
        "risks_and_assumptions": rows(sections, "Risks and assumptions") if doc_type == "feature" else [],
        "open_questions": open_q,
        "conflicts": conflicts,
        "sources": rows(sections, "Source register"),
    }
    Path(sys.argv[2]).write_text(json.dumps(out, indent=2))
    print(f"Exported {len(requirements)} requirements, {len(open_q)} open questions, {len(out['sources'])} sources to {sys.argv[2]}")
    print(f"ready_for_design: {out['ready_for_design']}")


if __name__ == "__main__":
    main()
