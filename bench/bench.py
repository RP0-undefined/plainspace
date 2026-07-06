#!/usr/bin/env python3
"""Reproducible token benchmark for the Plainspace recall protocol.

Generates a deterministic synthetic knowledge base, then answers the same
questions three ways and reports tokens loaded + retrieval accuracy:

  (a) naive tree-crawl   — load every file
  (b) index-first        — load index.md, resolve to one file, open it
  (c) rung-2 FTS         — psindex search (<=5 candidates), open the top hit

Tokens are approximated as chars/4 (no tokenizer dependency), so numbers are
reproducible on any machine. Run: python3 bench/bench.py
"""

import contextlib
import io
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import psindex  # noqa: E402

N_DOCS = 40
TOPICS = [
    "pricing", "onboarding", "billing", "refunds", "sso", "residency",
    "roadmap", "security", "api-limits", "webhooks", "sla", "uptime",
    "support-tiers", "data-export", "gdpr", "retention", "encryption",
    "backups", "migrations", "sandbox", "rate-limits", "audit-log",
    "permissions", "roles", "provisioning", "deprovisioning", "invoicing",
    "taxes", "currencies", "discounts", "trials", "seats", "quotas",
    "integrations", "slack", "email", "analytics", "funnel", "churn", "nps",
]


def approx_tokens(text):
    return (len(text) + 3) // 4


def gen_corpus(root):
    (root / "knowledge").mkdir(parents=True)
    for i, topic in enumerate(TOPICS[:N_DOCS]):
        fact = f"The {topic} value for cohort {i:02d} is unique-code-{i:02d}{topic}."
        (root / "knowledge" / f"{topic}.md").write_text(
            f"---\ntype: Reference\ntitle: {topic.title()}\n"
            f"description: Facts about {topic}.\ntags: [{topic}]\n---\n\n"
            f"- {fact}\n- See also the {TOPICS[(i+1) % N_DOCS]} policy.\n")
    # hand-written root map (what an agent reads first)
    lines = ["# Knowledge"]
    for topic in TOPICS[:N_DOCS]:
        lines.append(f"* [{topic.title()}](knowledge/{topic}.md) — Facts about {topic}.")
    (root / "index.md").write_text("\n".join(lines) + "\n")


def questions():
    # (query, expected file) — ask for each topic's unique fact
    return [(t, f"knowledge/{t}.md") for t in TOPICS[:N_DOCS]]


def naive(root, _q):
    total = sum(approx_tokens(p.read_text()) for p, _ in psindex.iter_concepts(root))
    return total, True  # loads everything → always has the answer


def index_first(root, query):
    index = (root / "index.md").read_text()
    toks = approx_tokens(index)
    # resolve: the map line with the most query-word overlap
    best, best_score = None, -1
    for line in index.splitlines():
        if "](" not in line:
            continue
        path = line.split("](", 1)[1].split(")", 1)[0]
        score = sum(w in line.lower() for w in query.lower().split())
        if score > best_score:
            best, best_score = path, score
    if best:
        toks += approx_tokens((root / best).read_text())
    return toks, best == f"knowledge/{query}.md"


def rung2(root, query):
    psindex.ensure_fresh(root)
    import sqlite3
    db = sqlite3.connect(root / psindex.DB_NAME)
    match = " ".join(re.findall(r"\w+", query))  # FTS-safe terms (drop hyphens etc.)
    rows = db.execute(
        "SELECT f.path, f.title, f.description FROM fts JOIN files f ON f.path=fts.path "
        "WHERE fts MATCH ? ORDER BY bm25(fts) LIMIT 5", (match,)).fetchall()
    db.close()
    toks = approx_tokens("".join(f"{p} {t} {d}" for p, t, d in rows))  # candidate lines
    if rows:
        toks += approx_tokens((root / rows[0][0]).read_text())         # open top hit
    hit = bool(rows) and rows[0][0] == f"knowledge/{query}.md"
    return toks, hit


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        gen_corpus(root)
        with contextlib.redirect_stdout(io.StringIO()):
            psindex.build(root)                 # one-time index build, silenced
        qs = questions()
        strategies = [("naive tree-crawl", naive),
                      ("index-first", index_first),
                      ("rung-2 FTS", rung2)]
        print(f"corpus: {N_DOCS} docs, {len(qs)} questions, tokens ~= chars/4\n")
        print("| strategy | avg tokens/query | accuracy |")
        print("|----------|------------------|----------|")
        for name, fn in strategies:
            toks, hits = zip(*(fn(root, q) for q, _ in qs))
            print(f"| {name} | {sum(toks)//len(toks)} | "
                  f"{100*sum(hits)//len(hits)}% |")


if __name__ == "__main__":
    main()
