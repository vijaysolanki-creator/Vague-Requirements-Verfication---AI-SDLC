#!/usr/bin/env python3
"""Verify every non-skipped file appears in its module doc, plus style checks.

Usage: python verify_coverage.py <output_folder>
Writes <output_folder>/_coverage.md. Exit code 1 if anything is missing.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

REQUIRED = ["## Purpose", "## Features", "## Files", "## Dependencies", "## Data flow", "## Keywords"]
EM_DASH = "\u2014"


def slug(module):
    return module.replace("/", "-").replace("\\", "-")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    out = Path(sys.argv[1]).resolve()
    manifest = json.loads((out / "_manifest.json").read_text())
    files, skipped = manifest["files"], manifest["skipped"]

    by_mod = defaultdict(list)
    for f in files:
        by_mod[f["module"]].append(f["path"])

    missing_files, no_doc, bad_sections = [], [], []
    per_mod = {}
    for mod, paths in sorted(by_mod.items()):
        doc = out / "modules" / f"{slug(mod)}.md"
        if not doc.exists():
            no_doc.append(mod)
            missing_files += paths
            per_mod[mod] = (0, len(paths))
            continue
        text = doc.read_text()
        absent = [p for p in paths if f"`{p}`" not in text]
        missing_files += absent
        per_mod[mod] = (len(paths) - len(absent), len(paths))
        gaps = [h for h in REQUIRED if h not in text]
        if gaps:
            bad_sections.append((mod, gaps))

    system_missing = [n for n in ("README.md", "architecture.md", "glossary.md") if not (out / n).exists()]
    dashes = [str(p.relative_to(out)) for p in out.rglob("*.md")
              if p.name != "_coverage.md" and EM_DASH in p.read_text()]

    total = len(files)
    done = total - len(missing_files)
    pct = 100 if total == 0 else round(done * 100 / total, 1)

    L = ["# Coverage", "", f"Files covered: {done} / {total} ({pct}%)", f"Skipped: {len(skipped)}", "",
         "## Per module", "", "| Module | Covered | Total |", "|---|---|---|"]
    L += [f"| {m} | {d} | {t} |" for m, (d, t) in per_mod.items()]
    L += ["", "## Modules without a doc"] + ([f"- {m}" for m in no_doc] or ["None"])
    L += ["", "## Files missing from their module doc"] + ([f"- {p}" for p in missing_files] or ["None"])
    L += ["", "## Module docs missing sections"] + ([f"- {m}: {', '.join(g)}" for m, g in bad_sections] or ["None"])
    L += ["", "## Missing system docs"] + ([f"- {n}" for n in system_missing] or ["None"])
    L += ["", "## Docs containing em dashes"] + ([f"- {p}" for p in dashes] or ["None"])
    L += ["", "## Skipped files", "", "| Path | Reason |", "|---|---|"]
    L += [f"| {s['path']} | {s['reason']} |" for s in skipped] or ["| None | |"]
    (out / "_coverage.md").write_text("\n".join(L) + "\n")

    print(f"Covered {done}/{total} ({pct}%)")
    for label, items in (("modules without doc", no_doc), ("files missing", missing_files),
                         ("docs missing sections", bad_sections), ("system docs missing", system_missing),
                         ("em dashes", dashes)):
        if items:
            print(f"  {label}: {len(items)}")
    ok = not (no_doc or missing_files or bad_sections or system_missing or dashes)
    print("PASS" if ok else "FAIL: fix and rerun")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
