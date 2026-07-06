#!/usr/bin/env python3
"""pssearch3 — rung 3: hybrid BM25 + embeddings recall, behind the same verb.

Fuses FTS5 (BM25) rank with vector rank via Reciprocal Rank Fusion. Embeddings
come from any OpenAI-compatible /v1/embeddings endpoint (env-configured); vectors
are cached in memory.db (still disposable). With NO backend configured, it falls
straight back to pure FTS (rung 2) — the workspace stays fully functional.

  pssearch3.py index  [workspace]                    embed + cache all concepts
  pssearch3.py search QUERY... [--dir WS] [--all]     hybrid search
                      [--limit N] [--since DATE]

Env: PSSEARCH_EMBED_URL, PSSEARCH_EMBED_MODEL, PSSEARCH_API_KEY (optional).
Stdlib only. Same output format, archive exclusion, and "files win" law as psindex.
"""

import argparse
import json
import math
import os
import re
import sqlite3
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psindex  # noqa: E402

RRF_K = 60


def backend():
    url = os.environ.get("PSSEARCH_EMBED_URL")
    return url, os.environ.get("PSSEARCH_EMBED_MODEL", "text-embedding-3-small")


def embed(texts):
    """Return list[list[float]] from the configured endpoint, or None if unavailable."""
    url, model = backend()
    if not url:
        return None
    body = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    key = os.environ.get("PSSEARCH_API_KEY")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        return [d["embedding"] for d in data["data"]]
    except Exception as e:  # network/endpoint/shape — degrade, never crash recall
        print(f"[pssearch3] embedding backend unavailable ({e}); FTS-only.",
              file=sys.stderr)
        return None


def _ensure_vec_table(db):
    db.execute("CREATE TABLE IF NOT EXISTS vec(path TEXT PRIMARY KEY, data TEXT)")


def index(root):
    psindex.ensure_fresh(root)
    db = sqlite3.connect(root / psindex.DB_NAME)
    _ensure_vec_table(db)
    rows = db.execute("SELECT path, title, description, body FROM files").fetchall()
    texts = [f"{t or ''}\n{d or ''}\n{b or ''}" for _, t, d, b in rows]
    vecs = embed(texts)
    if vecs is None:
        db.close()
        sys.exit("no embedding backend configured (set PSSEARCH_EMBED_URL); nothing indexed")
    db.execute("DELETE FROM vec")
    for (path, *_), v in zip(rows, vecs):
        db.execute("INSERT OR REPLACE INTO vec VALUES(?,?)", (path, json.dumps(v)))
    db.commit()
    db.close()
    print(f"embedded {len(vecs)} concepts")


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _fts_ranked(db, query):
    terms = " ".join(re.findall(r"\w+", query))
    if not terms:
        return []
    return [r[0] for r in db.execute(
        "SELECT path FROM fts WHERE fts MATCH ? ORDER BY bm25(fts)", (terms,)).fetchall()]


def _vec_ranked(db, query):
    have = db.execute("SELECT 1 FROM sqlite_master WHERE name='vec'").fetchone()
    if not have:
        return []
    qv = embed([query])
    if not qv:
        return []
    scored = []
    for path, data in db.execute("SELECT path, data FROM vec").fetchall():
        scored.append((_cosine(qv[0], json.loads(data)), path))
    scored.sort(reverse=True)
    return [p for _, p in scored]


def search(root, query, show_all=False, limit=5, since=None):
    psindex.ensure_fresh(root)
    db = sqlite3.connect(root / psindex.DB_NAME)
    has_fts = db.execute("SELECT 1 FROM sqlite_master WHERE name='fts'").fetchone()
    if not has_fts:                                   # no FTS5 → defer to psindex fallback
        db.close()
        return psindex.search(root, query, show_all=show_all, limit=limit, since=since)

    fts, vec = _fts_ranked(db, query), _vec_ranked(db, query)
    scores = {}
    for ranked in (fts, vec):
        for rank, path in enumerate(ranked):
            scores[path] = scores.get(path, 0.0) + 1.0 / (RRF_K + rank)
    order = sorted(scores, key=lambda p: scores[p], reverse=True)

    meta = {r[0]: r for r in db.execute(
        "SELECT path, type, title, description, status, updated, last_verified "
        "FROM files").fetchall()}
    shown = 0
    for path in order:
        _, typ, title, desc, status, updated, verified = meta[path]
        if not show_all and (status in ("superseded", "archived", "consolidated")
                             or path.startswith("archive/")):
            continue
        if not psindex._since_ok(updated, verified, since):
            continue
        print(f"{path}  [{typ or '?'}]  {title or Path(path).stem} — {desc or ''}")
        shown += 1
        if shown >= limit:
            break
    db.close()
    if shown == 0:
        print("no results (try --all to include archive, or widen --since)")


def main():
    ap = argparse.ArgumentParser(prog="pssearch3.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_i = sub.add_parser("index"); p_i.add_argument("workspace", nargs="?", default=".")
    p_s = sub.add_parser("search")
    p_s.add_argument("query", nargs="+")
    p_s.add_argument("--dir", default=".")
    p_s.add_argument("--all", action="store_true")
    p_s.add_argument("--limit", type=int, default=5)
    p_s.add_argument("--since", default=None)
    a = ap.parse_args()
    if a.cmd == "index":
        index(Path(a.workspace).resolve())
    else:
        search(Path(a.dir).resolve(), " ".join(a.query),
               show_all=a.all, limit=a.limit, since=a.since)


if __name__ == "__main__":
    main()
