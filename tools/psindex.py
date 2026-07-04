#!/usr/bin/env python3
"""psindex — disposable SQLite index over a Plainspace workspace.

Files are the source of truth; memory.db is a rebuildable cache (delete it
freely). Stdlib only. FTS5 when available, LIKE fallback otherwise.

Usage:
  psindex.py build  [workspace]                  rebuild memory.db
  psindex.py search "query" [--dir WS] [--all]   search (archive excluded unless --all)
  psindex.py map    [workspace] [--force]        regenerate per-directory index.md maps
"""

import re
import sqlite3
import sys
from pathlib import Path

DB_NAME = "memory.db"
RESERVED = {"index.md", "log.md"}
SKIP_PARTS = {".git", "node_modules", "tools"}
MARKER = "<!-- generated: psindex map -->"


def parse_frontmatter(text):
    """Tolerant parser for the subset of YAML Plainspace uses. Returns (meta, body)."""
    meta, body = {}, text
    if not text.startswith("---"):
        return meta, body
    end = text.find("\n---", 3)
    if end == -1:
        return meta, body
    body = text[end + 4:]
    key = None
    for line in text[3:end].splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                val = ", ".join(v.strip() for v in val[1:-1].split(",") if v.strip())
            elif val in (">", "|", ">-", "|-"):
                val = ""
            meta[key] = val
        elif key and line.lstrip().startswith("- "):
            item = line.lstrip()[2:].split("#")[0].strip()
            meta[key] = f"{meta[key]}, {item}".lstrip(", ") if meta[key] else item
        elif key and line.startswith(" "):
            meta[key] = f"{meta[key]} {line.strip()}".strip()
    return meta, body


def iter_concepts(root):
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if rel.parts and (set(rel.parts[:-1]) & SKIP_PARTS):
            continue
        if p.name.lower() in RESERVED or p.name.startswith("."):
            continue
        yield p, rel


def build(root):
    db_path = root / DB_NAME
    db = sqlite3.connect(db_path)
    db.executescript(
        """
        DROP TABLE IF EXISTS files;
        CREATE TABLE files(
            path TEXT PRIMARY KEY, type TEXT, title TEXT, description TEXT,
            audience TEXT, status TEXT, tags TEXT, updated TEXT, source TEXT);
        """
    )
    fts = True
    try:
        db.executescript(
            "DROP TABLE IF EXISTS fts;"
            "CREATE VIRTUAL TABLE fts USING fts5("
            "path UNINDEXED, title, description, tags, body);"
        )
    except sqlite3.OperationalError:
        fts = False
    n = 0
    for p, rel in iter_concepts(root):
        meta, body = parse_frontmatter(p.read_text(errors="replace"))
        db.execute(
            "INSERT OR REPLACE INTO files VALUES(?,?,?,?,?,?,?,?,?)",
            (str(rel), meta.get("type"), meta.get("title"), meta.get("description"),
             meta.get("audience"), meta.get("status"), meta.get("tags"),
             meta.get("updated"), meta.get("source")),
        )
        if fts:
            db.execute(
                "INSERT INTO fts VALUES(?,?,?,?,?)",
                (str(rel), meta.get("title", ""), meta.get("description", ""),
                 meta.get("tags", ""), body),
            )
        n += 1
    db.commit()
    db.close()
    note = "" if fts else " (FTS5 unavailable: search will use LIKE fallback)"
    print(f"indexed {n} files -> {db_path}{note}")


def search(root, query, show_all=False, limit=10):
    db_path = root / DB_NAME
    if not db_path.exists():
        build(root)
    db = sqlite3.connect(db_path)
    has_fts = db.execute(
        "SELECT 1 FROM sqlite_master WHERE name='fts'").fetchone() is not None
    terms = re.findall(r"\w+", query)
    if not terms:
        sys.exit("empty query")
    if has_fts:
        rows = db.execute(
            "SELECT f.path, f.type, f.title, f.description, f.status "
            "FROM fts JOIN files f ON f.path = fts.path "
            "WHERE fts MATCH ? ORDER BY bm25(fts) LIMIT ?",
            (" ".join(terms), limit * 5),
        ).fetchall()
    else:
        like = f"%{terms[0]}%"
        rows = db.execute(
            "SELECT path, type, title, description, status FROM files "
            "WHERE title LIKE ? OR description LIKE ? OR tags LIKE ? OR path LIKE ? "
            "LIMIT ?",
            (like, like, like, like, limit * 5),
        ).fetchall()
    shown = 0
    for path, typ, title, desc, status in rows:
        if not show_all:
            if status in ("superseded", "archived") or path.startswith("archive/"):
                continue
        print(f"{path}  [{typ or '?'}]  {title or Path(path).stem} — {desc or ''}")
        shown += 1
        if shown >= limit:
            break
    if shown == 0:
        print("no results (try --all to include archive)")


def build_maps(root, force=False):
    by_dir = {}
    for p, rel in iter_concepts(root):
        by_dir.setdefault(rel.parent, []).append(p)
    for d in sorted(by_dir):
        target = root / d / "index.md"
        if target.exists() and MARKER not in target.read_text() and not force:
            print(f"skip {target.relative_to(root)} (hand-written; --force to overwrite)")
            continue
        name = "Workspace" if str(d) == "." else str(d)
        lines = [MARKER, f"# {name} — map", ""]
        for p in sorted(by_dir[d]):
            meta, _ = parse_frontmatter(p.read_text(errors="replace"))
            title = meta.get("title") or p.stem
            desc = meta.get("description", "")
            lines.append(f"* [{title}]({p.name}) — {desc}")
        subdirs = sorted(x for x in by_dir if x.parent == d and x != d)
        if subdirs:
            lines += ["", "## Subdirectories"]
            lines += [f"* [{s.name}/]({s.name}/index.md)" for s in subdirs]
        target.write_text("\n".join(lines) + "\n")
        print(f"wrote {target.relative_to(root)}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    cmd, rest = args[0], args[1:]
    flags = {a for a in rest if a.startswith("--")}
    pos = [a for a in rest if not a.startswith("--")]
    if "--dir" in flags:  # search --dir WS form: value is next positional-like token
        i = rest.index("--dir")
        flags.discard("--dir")
        wsdir = rest[i + 1]
        pos = [a for a in pos if a != wsdir]
    else:
        wsdir = None

    if cmd == "build":
        build(Path(pos[0] if pos else ".").resolve())
    elif cmd == "search":
        if not pos:
            sys.exit('usage: psindex.py search "query" [--dir WS] [--all]')
        search(Path(wsdir or ".").resolve(), " ".join(pos), show_all="--all" in flags)
    elif cmd == "map":
        build_maps(Path(pos[0] if pos else ".").resolve(), force="--force" in flags)
    else:
        sys.exit(f"unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
