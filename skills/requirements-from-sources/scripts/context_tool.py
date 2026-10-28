#!/usr/bin/env python3
"""Context engineering helper (standard library only).

Usage:
  context_tool.py init <project_dir>
  context_tool.py discover <project_dir> [--name "Project"] [--out candidates.json] [--draft]
  context_tool.py enable <context-sources.json> <id> [<id> ...]
  context_tool.py validate-config <context-sources.json>
  context_tool.py validate-pack <context-pack.json> [--config context-sources.json]

Exit code 1 on any ERROR. Warnings do not fail the run.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

METHODS = {"connector", "tool", "file", "url", "cli", "api", "paste", "other"}
TRUST = {"high", "medium", "low"}
FRESH = {"static", "dated", "live"}
SENS = {"none", "internal", "confidential", "pii"}
STATUS = {"searched", "skipped", "unavailable"}
SECRET = re.compile(
    r"(xox[baprs]-[A-Za-z0-9-]{8,}|sk-[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{10,}|AKIA[0-9A-Z]{16}"
    r"|ghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
ISO = "%Y-%m-%d"


def load(path):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        print(f"ERROR: file not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in {path}: {e}")
        sys.exit(1)


def is_date(s):
    try:
        datetime.strptime(s, ISO)
        return True
    except (ValueError, TypeError):
        return False


def finish(errors, warnings, summary):
    print(summary)
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print("PASS" if not errors else f"FAIL: {len(errors)} error(s)")
    sys.exit(1 if errors else 0)


def cmd_init(args):
    if not args:
        print(__doc__)
        sys.exit(1)
    project = Path(args[0]).resolve()
    project.mkdir(parents=True, exist_ok=True)
    target = project / "context-sources.json"
    if target.exists():
        print(f"Registry already exists, not overwriting: {target}")
        return
    example = Path(__file__).resolve().parent.parent / "references" / "context-sources.example.json"
    shutil.copy(example, target)
    (project / "requirements").mkdir(exist_ok=True)
    print(f"Created {target}")
    print("Next: replace the example entries with the project's real sources, set enabled to true, then run validate-config.")


SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "dist", "build", "__pycache__", ".next", "target", ".idea", ".vscode"}
MAX_DEPTH, MAX_FILES = 4, 4000

# category -> (kind, covers, freshness, name patterns on lowercase file or dir names)
CATEGORIES = [
    ("specs", "document", ["requirements", "specs", "design decisions"], "static",
     re.compile(r"(^|[-_ ])(prd|brd|spec|specs|requirement|requirements|design|rfc|proposal)([-_ .]|$)")),
    ("adr", "decision record", ["architecture decisions"], "static",
     re.compile(r"(^adr$|^adrs$|^decisions?$|^adr[-_ ]?\d+)")),
    ("docs", "documentation", ["product behavior", "setup", "architecture"], "dated",
     re.compile(r"(^readme|^docs?$|^documentation$|^wiki$|^changelog|^architecture)")),
    ("api", "api spec", ["interfaces", "data contracts"], "dated",
     re.compile(r"(openapi|swagger|\.proto$|schema\.graphql$)")),
    ("tickets", "ticket export", ["backlog", "bugs", "feature requests"], "dated",
     re.compile(r"(jira|backlog|tickets?|issues?)([-_ .]|$)")),
    ("meetings", "meeting transcript", ["decisions", "requirements stated"], "static",
     re.compile(r"(meeting|transcript|minutes|standup|workshop)|\.(vtt|srt)$")),
    ("chat_email", "chat or email export", ["client requests", "approvals"], "dated",
     re.compile(r"(slack|teams|discord|chat)[-_ ]?(export)?|\.(eml|mbox)$")),
    ("design", "design file", ["ui flows", "mockups"], "dated",
     re.compile(r"(\.fig$|\.sketch$|^designs?$|^mockups?$|^wireframes?$)")),
]
DOC_EXT = {".md", ".txt", ".rst", ".adoc", ".pdf", ".docx", ".csv", ".json", ".yaml", ".yml", ".vtt", ".srt", ".eml", ".mbox", ".fig", ".sketch", ".proto", ".graphql", ""}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "source"


def clean_url(url):
    """Strip credentials from a git remote so tokens never reach outputs."""
    return re.sub(r"//[^/@\s]+@", "//", url)


def first_heading(path):
    try:
        with open(path, "r", errors="ignore") as f:
            for _ in range(30):
                line = f.readline()
                if not line:
                    break
                if line.startswith("#"):
                    return line.lstrip("# ").strip()[:80]
    except OSError:
        pass
    return ""


def project_terms(root, name):
    terms = []

    def add(t):
        t = str(t).strip()
        if t and len(t) > 2 and t.lower() not in {x.lower() for x in terms}:
            terms.append(t)

    if name:
        add(name)
    add(root.name)
    try:
        out = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            add(Path(clean_url(out.stdout.strip())).stem)
    except (OSError, subprocess.SubprocessError):
        pass
    pkg = root / "package.json"
    if pkg.exists():
        try:
            add(json.loads(pkg.read_text()).get("name", ""))
        except (OSError, json.JSONDecodeError):
            pass
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        m = re.search(r'^name\s*=\s*"([^"]+)"', pyproject.read_text(errors="ignore"), re.M)
        if m:
            add(m.group(1))
    for readme in ("README.md", "readme.md", "README.rst"):
        if (root / readme).exists():
            add(first_heading(root / readme))
            break
    return terms


def scan_local(root):
    found, count = {}, 0
    for dirpath, dirnames, filenames in os.walk(root):
        depth = Path(dirpath).relative_to(root).parts
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and len(depth) < MAX_DEPTH]
        entries = [(d, True) for d in dirnames] + [(f, False) for f in filenames]
        for entry, is_dir in entries:
            count += 1
            if count > MAX_FILES:
                return found, True
            low = entry.lower()
            ext = Path(entry).suffix.lower()
            if not is_dir and ext not in DOC_EXT:
                continue
            for cat, kind, covers, fresh, pat in CATEGORIES:
                if pat.search(low):
                    rel = str((Path(dirpath) / entry).relative_to(root))
                    item = found.setdefault(cat, {"kind": kind, "covers": covers, "freshness": fresh, "paths": []})
                    if len(item["paths"]) < 8:
                        item["paths"].append(rel + ("/" if is_dir else ""))
                    break
    return found, False


def cmd_discover(args):
    if not args:
        print(__doc__)
        sys.exit(1)
    root = Path(args[0]).resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}")
        sys.exit(1)
    name = args[args.index("--name") + 1] if "--name" in args else ""
    out = args[args.index("--out") + 1] if "--out" in args else ""
    terms = project_terms(root, name)
    found, truncated = scan_local(root)

    candidates = []
    for cat, item in found.items():
        candidates.append({
            "id": f"local-{slug(cat)}",
            "name": f"Local {cat} files",
            "kind": item["kind"],
            "access": {"method": "file", "hint": "Files in the project folder"},
            "location": ", ".join(item["paths"][:3]),
            "paths": item["paths"],
            "covers": item["covers"],
            "freshness": item["freshness"],
            "confidence": "medium" if cat in ("specs", "adr", "tickets", "meetings") else "low",
        })
    result = {"project_terms": terms, "candidates": candidates, "scan_truncated": truncated,
              "note": "Metadata only. Connector sources (wiki, tickets, chat, email, drive) are probed by the agent with user consent."}

    print(f"Project terms: {terms if terms else 'none found, ask the user for the project name'}")
    if not candidates:
        print("No local candidate sources found.")
    for c in candidates:
        print(f"- {c['id']} ({c['kind']}, confidence {c['confidence']}): {', '.join(c['paths'][:4])}")
    if truncated:
        print(f"WARN: scan stopped after {MAX_FILES} entries")
    if out:
        Path(out).write_text(json.dumps(result, indent=2))
        print(f"Wrote {out}")

    if "--draft" in args:
        target = root / "context-sources.json"
        if target.exists():
            print(f"Registry exists, not overwriting: {target}. Merge approved candidates by hand.")
            return
        today = date.today().strftime(ISO)
        sources = []
        for c in candidates:
            sources.append({
                "id": c["id"], "name": c["name"], "kind": c["kind"], "enabled": False,
                "access": c["access"], "location": c["location"], "covers": c["covers"],
                "trust": "medium", "freshness": c["freshness"], "sensitivity": "confidential",
                "owner": "TBD",
                "retrieval": {"time_window": "all", "queries_hint": ", ".join(terms[:3])},
                "discovered": {"by": "local scan", "date": today, "terms_matched": terms[:3],
                               "evidence": f"{len(c['paths'])} matching path(s)", "approved": False},
                "notes": "Proposed by discovery. Enable only after the user approves.",
            })
        cfg = {"version": 1, "project": name or (terms[0] if terms else root.name),
               "defaults": {"precedence": ["approved-document", "client-written", "decision-record", "internal-chat", "draft", "verbal"],
                            "max_items_per_source": 25, "redact": ["email", "phone", "api_key"],
                            "ask_before_unregistered": True, "stale_after_days": 14},
               "sources": sources}
        target.write_text(json.dumps(cfg, indent=2))
        (root / "requirements").mkdir(exist_ok=True)
        print(f"Wrote draft registry (all entries disabled): {target}")


def cmd_enable(args):
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    path, ids = args[0], set(args[1:])
    cfg = load(path)
    hit = set()
    for s in cfg.get("sources", []):
        if s.get("id") in ids:
            s["enabled"] = True
            if "discovered" in s:
                s["discovered"]["approved"] = True
            hit.add(s["id"])
    missing = ids - hit
    Path(path).write_text(json.dumps(cfg, indent=2))
    print(f"Enabled: {sorted(hit)}")
    if missing:
        print(f"ERROR: unknown ids: {sorted(missing)}")
        sys.exit(1)


def cmd_validate_config(args):
    if not args:
        print(__doc__)
        sys.exit(1)
    raw = Path(args[0]).read_text() if Path(args[0]).exists() else ""
    cfg = load(args[0])
    errors, warnings = [], []

    if cfg.get("version") != 1:
        errors.append("version must be 1")
    if not str(cfg.get("project", "")).strip():
        errors.append("project name is required")
    if SECRET.search(raw):
        errors.append("file appears to contain a credential; store secrets outside the registry")

    defaults = cfg.get("defaults", {})
    sources = cfg.get("sources", [])
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        sources = []

    ids, enabled = set(), 0
    needs_redact = False
    for i, s in enumerate(sources):
        sid = s.get("id", "")
        label = sid or f"sources[{i}]"
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", sid):
            errors.append(f"{label}: id must be a lowercase slug (letters, digits, hyphens)")
        if sid in ids:
            errors.append(f"{label}: duplicate id")
        ids.add(sid)
        for k in ("name", "kind"):
            if not str(s.get(k, "")).strip():
                errors.append(f"{label}: missing '{k}'")
        method = s.get("access", {}).get("method", "")
        if not method:
            errors.append(f"{label}: access.method is required")
        elif method not in METHODS:
            warnings.append(f"{label}: access.method '{method}' is not one of {sorted(METHODS)}")
        if not s.get("covers"):
            errors.append(f"{label}: 'covers' must list what this source can answer")
        if s.get("trust") not in TRUST:
            errors.append(f"{label}: trust must be one of {sorted(TRUST)}")
        if s.get("freshness") not in FRESH:
            errors.append(f"{label}: freshness must be one of {sorted(FRESH)}")
        sens = s.get("sensitivity", "none")
        if sens not in SENS:
            errors.append(f"{label}: sensitivity must be one of {sorted(SENS)}")
        if sens in ("confidential", "pii"):
            needs_redact = True
        if not s.get("owner"):
            warnings.append(f"{label}: no owner (who can answer questions about this source?)")
        if s.get("enabled", True):
            enabled += 1
            disc = s.get("discovered")
            if disc is not None and disc.get("approved") is not True:
                errors.append(f"{label}: discovered source is enabled without user approval (set discovered.approved only after the user agrees)")
        if s.get("enabled", True) and str(s.get("owner", "")).strip().upper() == "TBD":
            warnings.append(f"{label}: owner is TBD, ask who owns this source")

    if sources and enabled == 0:
        warnings.append("all sources are disabled; set enabled to true on real entries, or run discovery (references/source-discovery.md)")
    if sources and all(str(x.get("id", "")).startswith("example-") for x in sources):
        warnings.append("registry still contains only example entries; run discovery or replace them with real sources")
    if needs_redact and not defaults.get("redact"):
        warnings.append("sensitive sources exist but defaults.redact is empty")

    finish(errors, warnings, f"Registry: {len(sources)} sources, {enabled} enabled")


def cmd_validate_pack(args):
    if not args:
        print(__doc__)
        sys.exit(1)
    pack_path = args[0]
    config = None
    if "--config" in args:
        config = load(args[args.index("--config") + 1])
    raw = Path(pack_path).read_text() if Path(pack_path).exists() else ""
    pack = load(pack_path)
    errors, warnings = [], []

    if SECRET.search(raw):
        errors.append("pack appears to contain a credential; remove it")
    for k in ("feature", "type", "created", "scope", "sources_searched", "items", "gaps"):
        if k not in pack:
            errors.append(f"missing top-level field '{k}'")
    if pack.get("type") not in ("feature", "bug"):
        errors.append("type must be 'feature' or 'bug'")
    created = pack.get("created", "")
    if not is_date(created):
        errors.append("created must be YYYY-MM-DD")
    else:
        age = (date.today() - datetime.strptime(created, ISO).date()).days
        stale = (config or {}).get("defaults", {}).get("stale_after_days", 14)
        if age > stale:
            warnings.append(f"pack is {age} days old (stale after {stale}); refresh live sources before reuse")

    searched_ids = set()
    for s in pack.get("sources_searched", []):
        rid = s.get("registry_id", "")
        if not rid:
            errors.append("a sources_searched entry has no registry_id")
            continue
        searched_ids.add(rid)
        st = s.get("status")
        if st not in STATUS:
            errors.append(f"{rid}: status must be one of {sorted(STATUS)}")
        if st == "searched" and not s.get("queries"):
            errors.append(f"{rid}: searched sources must record the queries used")
        if st in ("skipped", "unavailable") and not s.get("reason"):
            errors.append(f"{rid}: {st} sources must give a reason")

    reg_ids, enabled_ids = set(), set()
    if config:
        for s in config.get("sources", []):
            reg_ids.add(s.get("id"))
            if s.get("enabled", True):
                enabled_ids.add(s.get("id"))
        for rid in sorted(enabled_ids - searched_ids):
            errors.append(f"enabled registry source '{rid}' is not accounted for in sources_searched")
        for rid in sorted(searched_ids - reg_ids - {"user-provided"}):
            errors.append(f"sources_searched references unknown registry source '{rid}'")

    seen = set()
    items = pack.get("items", [])
    if not items:
        errors.append("items is empty (no evidence retrieved)")
    for it in items:
        iid = it.get("id", "")
        if not re.fullmatch(r"S\d+", iid):
            errors.append(f"bad item id '{iid}' (expected S1, S2, ...)")
        if iid in seen:
            errors.append(f"duplicate item id {iid}")
        seen.add(iid)
        for k in ("registry_id", "kind", "title", "locator", "summary"):
            if not str(it.get(k, "")).strip():
                errors.append(f"{iid}: missing '{k}'")
        if it.get("trust") not in TRUST:
            errors.append(f"{iid}: trust must be one of {sorted(TRUST)}")
        if it.get("freshness") not in FRESH:
            errors.append(f"{iid}: freshness must be one of {sorted(FRESH)}")
        if not is_date(it.get("retrieved", "")):
            errors.append(f"{iid}: retrieved must be YYYY-MM-DD")
        d = it.get("date", "unknown")
        if d != "unknown" and not is_date(d):
            errors.append(f"{iid}: date must be YYYY-MM-DD or 'unknown'")
        rid = it.get("registry_id")
        if rid and rid not in searched_ids and rid != "user-provided":
            errors.append(f"{iid}: registry_id '{rid}' is not listed in sources_searched")
        if rid == "user-provided" and config:
            warnings.append(f"{iid}: user-provided item, consider adding its source to the registry")
        for ex in it.get("excerpts", []):
            if len(ex) > 300:
                warnings.append(f"{iid}: excerpt over 300 characters (keep excerpts short)")
                break

    for g in pack.get("gaps", []):
        if not g.get("description"):
            errors.append("a gap entry has no description")

    finish(errors, warnings,
           f"Pack: {len(items)} items, {len(searched_ids)} sources accounted for, {len(pack.get('gaps', []))} gaps")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd, args = sys.argv[1], sys.argv[2:]
    {"init": cmd_init, "discover": cmd_discover, "enable": cmd_enable, "validate-config": cmd_validate_config, "validate-pack": cmd_validate_pack}.get(
        cmd, lambda a: (print(__doc__), sys.exit(1)))(args)


if __name__ == "__main__":
    main()
