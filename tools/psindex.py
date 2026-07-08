#!/usr/bin/env python3
"""psindex — disposable SQLite index over a Plainspace workspace.

Files are the source of truth; memory.db is a rebuildable cache (delete it
freely). Stdlib only. FTS5 when available, LIKE fallback otherwise.

  psindex.py build  [workspace]                          rebuild memory.db
  psindex.py search QUERY... [--dir WS] [--all]          search the workspace
                     [--limit N] [--since YYYY-MM-DD]
  psindex.py map    [workspace] [--force]                regenerate index.md maps
  psindex.py stats  [workspace]                          memory hygiene counters
  psindex.py check  [workspace]                          conformance check (CI exit code)
  psindex.py watermark [workspace]                        advance auto-capture watermark (Phase 9)
  psindex.py links  PATH [--dir WS]                       who references PATH / what it references

The db auto-rebuilds when any indexed file is newer than it, or the file count
changed — so "files win" is enforced, not just stated.
"""

import argparse
import glob as globmod
import json
import os
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

DB_NAME = "memory.db"
RESERVED = {"index.md", "log.md"}
SKIP_PARTS = {".git", "node_modules", "tools"}
MARKER = "<!-- generated: psindex map -->"
DEFAULT_TRIGGERS = {"inbox_files": 10, "oldest_days": 7}
FIELDS = ("type", "title", "description", "audience", "status", "tags",
          "updated", "source", "last_verified", "derived_from")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REL_FIELDS = ("supersedes", "superseded_by", "derived_from", "promoted_to")


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


# --- link graph (Phase 10): relationships are first-class -----------------------
# Edges: concept body markdown links + frontmatter relations (supersedes/derived_from/
# promoted_to/superseded_by) + the root index.md `# Core` block. Generated maps are
# excluded (they mechanically link everything). Powers demotion + orphan detection.

def _resolve_link(src_rel, target):
    """Resolve a link target to a workspace-relative .md path, or None."""
    target = target.split("#")[0].strip()
    if not target or "://" in target or target.startswith(("mailto:", "#")):
        return None
    p = target.lstrip("/") if target.startswith("/") \
        else os.path.normpath(str(src_rel.parent / target))
    return p if p.endswith(".md") else None


def _concept_edges(rel, meta, body):
    """(dst, kind) edges out of one concept. Body links resolve relative to the
    concept's dir; frontmatter relation paths are workspace-relative."""
    out = []
    for m in LINK_RE.finditer(body):
        dst = _resolve_link(rel, m.group(1))
        if dst:
            out.append((dst, "link"))
    for field in REL_FIELDS:
        for t in (x.strip() for x in (meta.get(field) or "").split(",") if x.strip()):
            dst = os.path.normpath(t.lstrip("/"))
            if dst.endswith(".md"):
                out.append((dst, field))
    return out


def collect_edges(root):
    """All (src, dst, kind) edges + the set of concept paths. src='index.md' for Core."""
    edges, concepts = [], set()
    items = []
    for p, rel in iter_concepts(root):
        meta, body = parse_frontmatter(p.read_text(errors="replace"))
        concepts.add(str(rel))
        items.append((rel, meta, body))
    for rel, meta, body in items:
        edges += [(str(rel), dst, kind) for dst, kind in _concept_edges(rel, meta, body)]
    idx = root / "index.md"                       # Core block only (above the map marker)
    if idx.exists():
        core = idx.read_text(errors="replace").split(MARKER)[0]
        for m in LINK_RE.finditer(core):
            dst = _resolve_link(Path("index.md"), m.group(1))
            if dst:
                edges.append(("index.md", dst, "core"))
    return edges, concepts


def link_metrics(root):
    """(inbound, outbound) maps over existing concepts (broken links excluded)."""
    edges, concepts = collect_edges(root)
    inbound = {c: set() for c in concepts}
    outbound = {c: set() for c in concepts}
    for src, dst, _ in edges:
        if dst in concepts:
            inbound[dst].add(src)
            if src in concepts:
                outbound[src].add(dst)
    return inbound, outbound


def build(root):
    db_path = root / DB_NAME
    db = sqlite3.connect(db_path)
    cols = ", ".join(f"{c} TEXT" for c in FIELDS)
    db.executescript(
        f"DROP TABLE IF EXISTS files;"
        f"CREATE TABLE files(path TEXT PRIMARY KEY, {cols}, body TEXT);"
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
    placeholders = ", ".join("?" * (len(FIELDS) + 2))
    n = 0
    for p, rel in iter_concepts(root):
        meta, body = parse_frontmatter(p.read_text(errors="replace"))
        row = [str(rel)] + [meta.get(c) for c in FIELDS] + [body]
        db.execute(f"INSERT OR REPLACE INTO files VALUES({placeholders})", row)
        if fts:
            db.execute(
                "INSERT INTO fts VALUES(?,?,?,?,?)",
                (str(rel), meta.get("title", ""), meta.get("description", ""),
                 meta.get("tags", ""), body),
            )
        n += 1
    db.executescript("DROP TABLE IF EXISTS links;"
                     "CREATE TABLE links(src TEXT, dst TEXT, kind TEXT);")
    edges, _ = collect_edges(root)
    db.executemany("INSERT INTO links VALUES(?,?,?)", edges)
    db.commit()
    db.close()
    note = "" if fts else " (FTS5 unavailable: search will use LIKE fallback)"
    print(f"indexed {n} files -> {db_path}{note}")


def is_stale(root):
    """True if the db is missing, older than any concept file, or the count changed."""
    db_path = root / DB_NAME
    if not db_path.exists():
        return True
    db_mtime = db_path.stat().st_mtime
    disk, newest = 0, 0.0
    for p, _ in iter_concepts(root):
        disk += 1
        newest = max(newest, p.stat().st_mtime)
    if newest > db_mtime:
        return True
    try:
        db = sqlite3.connect(db_path)
        indexed = db.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        db.close()
    except sqlite3.Error:
        return True
    return indexed != disk


def ensure_fresh(root):
    if is_stale(root):
        build(root)


def _since_ok(row_updated, row_verified, since):
    if not since:
        return True
    newest = max((v or "")[:10] for v in (row_updated, row_verified))
    return newest >= since


def search(root, query, show_all=False, limit=5, since=None):
    ensure_fresh(root)
    db = sqlite3.connect(root / DB_NAME)
    has_fts = db.execute(
        "SELECT 1 FROM sqlite_master WHERE name='fts'").fetchone() is not None
    terms = re.findall(r"\w+", query)
    if not terms:
        sys.exit("empty query")
    sel = ("f.path, f.type, f.title, f.description, f.status, f.updated, "
           "f.last_verified")
    if has_fts:
        rows = db.execute(
            f"SELECT {sel} FROM fts JOIN files f ON f.path = fts.path "
            "WHERE fts MATCH ? ORDER BY bm25(fts) LIMIT ?",
            (" ".join(terms), limit * 5),
        ).fetchall()
    else:
        # AND of LIKEs across body + metadata, so minimal captures are findable.
        clause = " AND ".join(
            "(title LIKE ? OR description LIKE ? OR tags LIKE ? OR path LIKE ? "
            "OR body LIKE ?)" for _ in terms)
        params = [x for t in terms for x in ([f"%{t}%"] * 5)]
        rows = db.execute(
            f"SELECT {sel.replace('f.', '')} FROM files WHERE {clause} LIMIT ?",
            params + [limit * 5],
        ).fetchall()
    shown = 0
    for path, typ, title, desc, status, updated, verified in rows:
        if not show_all and (status in ("superseded", "archived", "consolidated")
                             or path.startswith("archive/")):
            continue
        if not _since_ok(updated, verified, since):
            continue
        print(f"{path}  [{typ or '?'}]  {title or Path(path).stem} — {desc or ''}")
        shown += 1
        if shown >= limit:
            break
    if shown == 0:
        print("no results (try --all to include archive, or widen --since)")
    db.close()


def build_maps(root, force=False):
    direct, dirs = {}, set()
    for p, rel in iter_concepts(root):
        direct.setdefault(rel.parent, []).append(p)
        d = rel.parent                       # register every ancestor dir up to root
        while True:
            dirs.add(d)
            if str(d) == ".":
                break
            d = d.parent
    for d in sorted(dirs, key=str):
        target = root / d / "index.md"
        prefix = ""
        if target.exists():
            existing = target.read_text()
            if MARKER in existing:
                prefix = existing.split(MARKER)[0]  # preserve content above marker
            elif force:
                prefix = ""                          # overwrite hand-written file
            else:
                print(f"skip {target.relative_to(root)} "
                      f"(hand-written, no marker; --force to convert)")
                continue
        name = "Workspace" if str(d) == "." else str(d)
        gen = [MARKER, f"# {name} — map", ""]
        concept_lines = []
        for p in sorted(direct.get(d, [])):
            meta, _ = parse_frontmatter(p.read_text(errors="replace"))
            concept_lines.append(f"* [{meta.get('title') or p.stem}]({p.name}) — "
                                 f"{meta.get('description', '')}")
        gen += concept_lines
        subdirs = sorted(x for x in dirs if x.parent == d and x != d)
        if subdirs:
            if concept_lines:
                gen.append("")
            gen += ["## Subdirectories"]
            gen += [f"* [{s.name}/]({s.name}/index.md)" for s in subdirs]
        target.write_text(prefix + "\n".join(gen) + "\n")
        print(f"wrote {target.relative_to(root)}")


def _days_ago(value):
    try:
        return (date.today() - date.fromisoformat(str(value)[:10])).days
    except (ValueError, TypeError):
        return None


def _capture_age(path, meta):
    """Age of a capture in days: updated frontmatter → <date>- filename → mtime."""
    for candidate in (_days_ago(meta.get("updated")),
                      _days_ago(re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
                                and re.match(r"(\d{4}-\d{2}-\d{2})", path.name).group(1))):
        if candidate is not None:
            return candidate
    return int((date.today() - date.fromtimestamp(path.stat().st_mtime)).days)


def read_triggers(root):
    trg = dict(DEFAULT_TRIGGERS)
    trg["warmup"] = False
    for stage in sorted(root.glob("9*_*/_stage.md")):
        meta, _ = parse_frontmatter(stage.read_text(errors="replace"))
        raw = meta.get("triggers", "")
        if not raw:
            continue
        for k in ("inbox_files", "oldest_days"):
            m = re.search(rf"{k}\s*:\s*(\d+)", raw)
            if m:
                trg[k] = int(m.group(1))
        trg["warmup"] = "warmup: true" in raw or "warmup:true" in raw
    return trg


# --- auto-capture (Phase 9): watermark over a harness transcript source -------
# Config lives on an optional `89_*/_stage.md` (source_glob + triggers.extract_turns);
# state lives in `.autocapture/watermark` (JSON: {abs_file: lines_processed}). Both
# derived/local — no external dependency, stdlib only.

def read_extract_config(root):
    """(source_glob, extract_turns) from an 89_*/_stage.md, or (None, None)."""
    for stage in sorted(root.glob("89_*/_stage.md")):
        meta, _ = parse_frontmatter(stage.read_text(errors="replace"))
        if not meta.get("source_glob"):
            continue
        m = re.search(r"extract_turns\s*:\s*(\d+)", meta.get("triggers", ""))
        return meta["source_glob"], (int(m.group(1)) if m else 5)
    return None, None


def _watermark_path(root):
    return root / ".autocapture" / "watermark"


def _read_watermark(root):
    p = _watermark_path(root)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (ValueError, OSError):
            return {}
    return {}


def _resolve_sources(root, source_glob):
    pattern = os.path.expanduser(source_glob)
    if not os.path.isabs(pattern):
        pattern = str(root / pattern)
    return sorted(globmod.glob(pattern))


def _linecount(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def extract_backlog(root):
    """(pending_turns, threshold) from watermark vs transcript source, or None."""
    source_glob, turns = read_extract_config(root)
    if not source_glob:
        return None
    wm = _read_watermark(root)
    pending = sum(max(0, _linecount(f) - int(wm.get(f, 0)))
                  for f in _resolve_sources(root, source_glob))
    return pending, turns


def advance_watermark(root):
    """Mark all current transcript lines processed (crash-safe: call AFTER writing captures)."""
    source_glob, _ = read_extract_config(root)
    if not source_glob:
        sys.exit("no 89_*/_stage.md with source_glob; nothing to watermark")
    wm = _read_watermark(root)
    before = 0
    for f in _resolve_sources(root, source_glob):
        lc = _linecount(f)
        before += max(0, lc - int(wm.get(f, 0)))
        wm[f] = lc
    p = _watermark_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(wm, sort_keys=True, indent=0) + "\n")
    print(f"watermark advanced (was {before} pending) -> {p.relative_to(root)}")


def stats(root):
    rows = [(p, rel, parse_frontmatter(p.read_text(errors="replace"))[0])
            for p, rel in iter_concepts(root)]
    if not rows:
        sys.exit("no concepts found")
    trg = read_triggers(root)

    by_top, by_status = {}, {}
    for _, rel, meta in rows:
        top = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        by_top[top] = by_top.get(top, 0) + 1
        by_status[meta.get("status") or "current"] = \
            by_status.get(meta.get("status") or "current", 0) + 1

    know = [(p, rel, m) for p, rel, m in rows if rel.parts[0] == "knowledge"]
    inbox = [(p, rel, m) for p, rel, m in rows if rel.parts[0] == "inbox"]
    # missing last_verified -> flag; verified today -> days_ago is 0, NOT stale
    # (do not use `... or 10**6`: 0 is falsy and would misflag today's facts).
    stale = [rel for _, rel, m in know
             if (d := _days_ago(m.get("last_verified"))) is None or d > 180]
    no_prov = [rel for _, rel, m in know if not m.get("derived_from") and not m.get("source")]
    inbound, outbound = link_metrics(root)
    # demotion candidate = unreferenced AND provably stale (last_verified present, >180d)
    demotion = [rel for _, rel, m in know
                if not inbound.get(str(rel))
                and (d := _days_ago(m.get("last_verified"))) is not None and d > 180]
    orphans = [rel for _, rel, m in know
               if not inbound.get(str(rel)) and not outbound.get(str(rel))]

    print(f"concepts: {len(rows)} ("
          + ", ".join(f"{k} {v}" for k, v in sorted(by_top.items())) + ")")
    print("status: " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))
    if inbox:
        oldest = max(_capture_age(p, m) for p, _, m in inbox)
        warm = trg["warmup"] and len(know) < 20
        thr_files = 3 if warm else trg["inbox_files"]
        due = len(inbox) >= thr_files or oldest > trg["oldest_days"]
        tag = f" <- CONSOLIDATE{' (warmup)' if warm else ''}" if due else ""
        print(f"inbox backlog: {len(inbox)} capture(s), oldest {oldest}d "
              f"(trigger: {thr_files} files / {trg['oldest_days']}d){tag}")
    else:
        print("inbox backlog: 0")
    eb = extract_backlog(root)
    if eb is not None:
        pending, turns = eb
        tag = " <- EXTRACT" if pending >= turns else ""
        print(f"extract backlog: {pending} pending turn(s) (trigger: {turns}){tag}")
    print(f"knowledge unverified >180d: {len(stale)}"
          + (" -> " + ", ".join(str(r) for r in stale[:5]) if stale else ""))
    print(f"knowledge lacking provenance (no derived_from/source): {len(no_prov)}"
          + (" -> " + ", ".join(str(r) for r in no_prov[:5]) if no_prov else ""))
    print(f"demotion candidates (unreferenced + >180d): {len(demotion)}"
          + (" -> " + ", ".join(str(r) for r in demotion[:5]) if demotion else ""))
    print(f"orphans (no links in/out): {len(orphans)}"
          + (" -> " + ", ".join(str(r) for r in orphans[:5]) if orphans else ""))


def links_cmd(root, target):
    """Print what references `target` (inbound) and what it references (outbound)."""
    db_path = root / DB_NAME
    if is_stale(root) or not db_path.exists():
        build(root)
    db = sqlite3.connect(db_path)
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='links'").fetchone():
        db.close()
        build(root)                                # db predates the links table
        db = sqlite3.connect(db_path)
    existing = {r[0] for r in db.execute("SELECT path FROM files").fetchall()}
    inb = db.execute("SELECT src, kind FROM links WHERE dst=? ORDER BY kind, src",
                     (target,)).fetchall()
    outb = db.execute("SELECT dst, kind FROM links WHERE src=? ORDER BY kind, dst",
                      (target,)).fetchall()
    db.close()
    print(f"inbound ({len(inb)}) — what references {target}:")
    for src, kind in inb:
        print(f"  <- {src} [{kind}]")
    print(f"outbound ({len(outb)}) — what {target} references:")
    for dst, kind in outb:
        broken = "" if (dst in existing or dst == "index.md") else "  (broken)"
        print(f"  -> {dst} [{kind}]{broken}")


def check(root):
    """Conformance check. Returns a list of problems; empty = conformant."""
    problems = []
    paths = {str(rel) for _, rel in iter_concepts(root)}
    for p, rel in iter_concepts(root):
        text = p.read_text(errors="replace")
        meta, _ = parse_frontmatter(text)
        if not (text.startswith("---") and text.find("\n---", 3) != -1):
            problems.append(f"{rel}: no parseable frontmatter")
            continue
        if not (meta.get("type") or "").strip():
            problems.append(f"{rel}: empty or missing `type`")
        for field in ("supersedes", "superseded_by"):
            tgt = meta.get(field)
            if tgt and tgt not in paths:
                problems.append(f"{rel}: {field} -> missing `{tgt}`")
        derived = meta.get("derived_from", "")
        for tgt in (x.strip() for x in derived.split(",") if x.strip()):
            if tgt not in paths:
                problems.append(f"{rel}: derived_from -> missing `{tgt}`")
    for pr in problems:
        print(pr)
    print(f"{'FAIL' if problems else 'OK'}: {len(problems)} problem(s)")
    return problems


def main():
    ap = argparse.ArgumentParser(prog="psindex.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def ws(p):
        p.add_argument("workspace", nargs="?", default=".")

    ws(sub.add_parser("build"))
    p_map = sub.add_parser("map"); ws(p_map); p_map.add_argument("--force", action="store_true")
    ws(sub.add_parser("stats"))
    ws(sub.add_parser("check"))
    ws(sub.add_parser("watermark"))
    p_l = sub.add_parser("links"); p_l.add_argument("path"); p_l.add_argument("--dir", default=".")
    p_s = sub.add_parser("search")
    p_s.add_argument("query", nargs="+")
    p_s.add_argument("--dir", default=".")
    p_s.add_argument("--all", action="store_true")
    p_s.add_argument("--limit", type=int, default=5)
    p_s.add_argument("--since", default=None)

    a = ap.parse_args()
    if a.cmd == "build":
        build(Path(a.workspace).resolve())
    elif a.cmd == "map":
        build_maps(Path(a.workspace).resolve(), force=a.force)
    elif a.cmd == "stats":
        stats(Path(a.workspace).resolve())
    elif a.cmd == "check":
        sys.exit(1 if check(Path(a.workspace).resolve()) else 0)
    elif a.cmd == "watermark":
        advance_watermark(Path(a.workspace).resolve())
    elif a.cmd == "links":
        links_cmd(Path(a.dir).resolve(), a.path)
    elif a.cmd == "search":
        search(Path(a.dir).resolve(), " ".join(a.query),
               show_all=a.all, limit=a.limit, since=a.since)


if __name__ == "__main__":
    main()
