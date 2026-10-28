#!/usr/bin/env python3
"""Verify every non-skipped file in the manifest has a doc, and run style checks.

Usage: python verify_coverage.py <output_folder>
Writes <output_folder>/_coverage.md. Exit code 1 if anything is missing.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

REQUIRED_HEADINGS = ["## Purpose", "## Features offered", "## Keywords", "## Dependencies", "## Data flow"]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    out = Path(sys.argv[1]).resolve()
    manifest = json.loads((out / "_manifest.json").read_text())
    files, skipped = manifest["files"], manifest["skipped"]

    missing, incomplete, dashes = [], [], []
    per_mod = defaultdict(lambda: [0, 0])
    for f in files:
        doc = out / f["module"] / "files" / (f["path"] + ".md")
        per_mod[f["module"]][1] += 1
        if not doc.exists():
            missing.append(f["path"])
            continue
        per_mod[f["module"]][0] += 1
        text = doc.read_text()
        gaps = [h for h in REQUIRED_HEADINGS if h not in text]
        if gaps:
            incomplete.append((f["path"], gaps))
        if "\u2014" in text:
            dashes.append(str(doc.relative_to(out)))

    no_overview = [m for m in per_mod if not (out / m / "overview.md").exists()]
    system_missing = [n for n in ("README.md", "architecture.md", "glossary.md") if not (out / n).exists()]
    for p in out.rglob("*.md"):
        if "\u2014" in p.read_text() and str(p.relative_to(out)) not in dashes:
            dashes.append(str(p.relative_to(out)))

    total = len(files)
    done = total - len(missing)
    pct = 100 if total == 0 else round(done * 100 / total, 1)

    lines = ["# Coverage", "", f"Documented: {done} / {total} ({pct}%)", f"Skipped: {len(skipped)}", ""]
    lines += ["## Per module", "", "| Module | Documented | Total |", "|---|---|---|"]
    lines += [f"| {m} | {d} | {t} |" for m, (d, t) in sorted(per_mod.items())]
    lines += ["", "## Missing file docs"] + ([f"- {p}" for p in missing] or ["None"])
    lines += ["", "## Docs missing required sections"] + ([f"- {p}: {', '.join(g)}" for p, g in incomplete] or ["None"])
    lines += ["", "## Modules without overview.md"] + ([f"- {m}" for m in no_overview] or ["None"])
    lines += ["", "## Missing system docs"] + ([f"- {n}" for n in system_missing] or ["None"])
    lines += ["", "## Docs containing em dashes"] + ([f"- {p}" for p in dashes] or ["None"])
    lines += ["", "## Skipped files", "", "| Path | Reason |", "|---|---|"]
    lines += [f"| {s['path']} | {s['reason']} |" for s in skipped] or ["| None | |"]
    (out / "_coverage.md").write_text("\n".join(lines) + "\n")

    print(f"Documented {done}/{total} ({pct}%)")
    for label, items in (("missing", missing), ("incomplete", incomplete), ("no overview", no_overview),
                         ("system docs missing", system_missing), ("em dashes", dashes)):
        if items:
            print(f"  {label}: {len(items)}")
    ok = not (missing or incomplete or no_overview or system_missing or dashes)
    print("PASS" if ok else "FAIL: fix and rerun")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
