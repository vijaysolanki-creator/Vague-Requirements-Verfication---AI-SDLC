#!/usr/bin/env python3
"""Build a manifest of every file in a repo, grouped by module and layer.

Usage: python inventory.py <repo_root> <output_folder> [--exclude dir1,dir2]
Writes <output_folder>/_manifest.json and _progress.md, prints a summary.
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", "out", ".next", ".nuxt", "target",
    "__pycache__", ".venv", "venv", "env", ".idea", ".vscode", "coverage",
    ".gradle", "bin", "obj", "vendor", ".cache", ".turbo", ".pytest_cache",
    ".mypy_cache", "site-packages",
}
SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Pipfile.lock", "composer.lock", "Cargo.lock", "go.sum", "Gemfile.lock",
    ".DS_Store",
}
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".pdf", ".zip",
    ".tar", ".gz", ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".mov",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar", ".pyc", ".bin", ".map",
    ".min.js", ".min.css",
}
FRONTEND_HINTS = {"frontend", "client", "web", "ui", "app", "pages", "components", "public", "views", "www"}
BACKEND_HINTS = {"backend", "server", "api", "services", "service", "controllers", "routes", "models", "db", "workers", "functions"}
FRONTEND_EXT = {".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss", ".sass", ".less", ".html"}
CONFIG_NAMES = {"dockerfile", "makefile", "docker-compose.yml", "docker-compose.yaml"}
CONFIG_EXT = {".json", ".yml", ".yaml", ".toml", ".ini", ".env", ".cfg", ".conf"}
MONOREPO_ROOTS = {"apps", "packages", "services", "libs", "modules"}
LANG = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (JSX)", ".ts": "TypeScript",
    ".tsx": "TypeScript (TSX)", ".java": "Java", ".kt": "Kotlin", ".cs": "C#", ".go": "Go",
    ".rb": "Ruby", ".php": "PHP", ".rs": "Rust", ".vue": "Vue", ".svelte": "Svelte",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".sql": "SQL", ".sh": "Shell",
    ".json": "JSON", ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".md": "Markdown",
    ".swift": "Swift", ".cpp": "C++", ".c": "C", ".h": "C/C++ header",
}


def module_of(parts):
    """Group by top-level dir; for monorepos use two levels."""
    if len(parts) == 1:
        return "_root"
    if parts[0] in MONOREPO_ROOTS and len(parts) > 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def layer_of(parts, ext, name):
    lower = [p.lower() for p in parts[:-1]]
    if any(p in ("test", "tests", "__tests__", "spec", "e2e") for p in lower) or \
       ".test." in name or ".spec." in name or name.startswith("test_"):
        return "test"
    if name.lower() in CONFIG_NAMES or (len(parts) == 1 and ext in CONFIG_EXT):
        return "config"
    if any(p in FRONTEND_HINTS for p in lower) or ext in FRONTEND_EXT:
        return "frontend"
    if any(p in BACKEND_HINTS for p in lower):
        return "backend"
    if any(p in ("shared", "common", "lib", "utils", "types") for p in lower):
        return "shared"
    return "backend" if ext in (".py", ".java", ".go", ".rb", ".php", ".cs", ".rs", ".kt", ".sql") else "shared"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    root = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    extra = set()
    if "--exclude" in sys.argv:
        extra = set(sys.argv[sys.argv.index("--exclude") + 1].split(","))
    out.mkdir(parents=True, exist_ok=True)
    try:
        out_rel = out.relative_to(root)
    except ValueError:
        out_rel = None

    files, skipped = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        if out_rel is not None and (rel_dir == out_rel or out_rel in rel_dir.parents):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and d not in extra]
        for fn in filenames:
            rel = (rel_dir / fn).as_posix() if str(rel_dir) != "." else fn
            parts = rel.split("/")
            ext = Path(fn).suffix.lower()
            if fn in SKIP_FILES:
                skipped.append({"path": rel, "reason": "lockfile"})
                continue
            if ext in BINARY_EXT or fn.endswith((".min.js", ".min.css")):
                skipped.append({"path": rel, "reason": "binary or minified asset"})
                continue
            try:
                size = (root / rel).stat().st_size
                if size > 1_500_000:
                    skipped.append({"path": rel, "reason": "file over 1.5 MB"})
                    continue
                with open(root / rel, "rb") as f:
                    if b"\0" in f.read(2048):
                        skipped.append({"path": rel, "reason": "binary content"})
                        continue
                with open(root / rel, "r", errors="ignore") as f:
                    lines = sum(1 for _ in f)
            except OSError:
                skipped.append({"path": rel, "reason": "unreadable"})
                continue
            files.append({
                "path": rel,
                "module": module_of(parts),
                "layer": layer_of(parts, ext, fn),
                "language": LANG.get(ext, ext.lstrip(".") or "text"),
                "lines": lines,
            })

    files.sort(key=lambda f: (f["module"], f["path"]))
    manifest = {"root": str(root), "output": str(out), "files": files, "skipped": skipped}
    (out / "_manifest.json").write_text(json.dumps(manifest, indent=2))

    by_mod = defaultdict(list)
    for f in files:
        by_mod[f["module"]].append(f)
    lines = ["# Progress", "", "Tick each file after its row is added to its module doc.", ""]
    for mod, fs in by_mod.items():
        lines.append(f"## {mod}")
        lines += [f"- [ ] {f['path']}" for f in fs]
        lines.append("")
    (out / "_progress.md").write_text("\n".join(lines))

    print(f"Files to document: {len(files)} | Skipped: {len(skipped)}")
    print(f"{'module':32} {'files':>5} {'lines':>8}  layers")
    for mod, fs in by_mod.items():
        layers = sorted({f['layer'] for f in fs})
        print(f"{mod:32} {len(fs):5d} {sum(f['lines'] for f in fs):8d}  {','.join(layers)}")
    print(f"\nManifest: {out / '_manifest.json'}")


if __name__ == "__main__":
    main()
