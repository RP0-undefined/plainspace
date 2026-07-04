---
type: Profile
audience: both
title: Plainspace Memory
description: >
  Long-term memory profile on top of the core spec: capture cheap, consolidate
  into knowledge, recall through a 3-rung ladder, forget into archive/. Scales
  from ten files to tens of thousands without changing agent behavior.
updated: 2026-07-04T00:00:00Z
---

# Plainspace Memory (profile)

Extends `SKILL.md`. Core rules (token principle, audience, index-first) remain law.
What core lacks for *memory* is a lifecycle. This profile adds it:

**capture → consolidate → recall → forget**

The three memory kinds map onto existing Plainspace layers:
episodic = `log.md` + `inbox/` · semantic = `knowledge/` · procedural = stages/playbooks.

---

## 1. Layout

```
workspace/
├── index.md              # map + optional curated "# Core" block (always loaded)
├── log.md                # episodic record, append-only, newest first
├── inbox/                # cheap captures, zero ceremony (§3)
├── knowledge/            # consolidated durable facts — semantic memory
├── playbooks/            # procedural memory (optional)
├── 90_consolidate/       # recurring maintenance stage (§4)
├── archive/              # superseded/stale facts — excluded from recall (§6)
├── tools/psindex.py      # optional derived index, rung 2 (§5)
└── memory.db             # DISPOSABLE cache — never the truth; gitignore it
```

---

## 2. Added frontmatter fields

| field           | applies to         | meaning |
|-----------------|--------------------|---------|
| `status`        | knowledge, archive | `current` (default) \| `superseded` \| `archived` |
| `supersedes`    | knowledge          | path of the fact this one replaced |
| `superseded_by` | archive            | path of the replacement |
| `source`        | any                | provenance: URL, email id, `"call 2026-07-04"`, … |
| `confidence`    | any                | `high` \| `medium` \| `low` |
| `last_verified` | knowledge          | ISO date the fact was last confirmed true |

---

## 3. Capture — writes must cost nothing

- Mid-task, write observations to `inbox/<date>-<slug>.md`. Frontmatter: `type: Capture`, `source`. Body: one fact per line.
- Do NOT update `index.md`. Do NOT format into a concept. Do NOT deduplicate.
- Rationale: any ceremony at capture time and the agent stops saving. `inbox/` is a buffer, not storage — consolidation empties it.

---

## 4. Consolidate — the stage that makes it a memory

Lives at `90_consolidate/_stage.md`. Run on cadence (daily/weekly) or when `inbox/` ≥ ~10 files.

- **Promote**: each inbox fact → create/extend a concept in `knowledge/` (carry `source`, `confidence`).
- **Supersede**: on contradiction, newer wins unless its `confidence` is lower. Loser moves to `archive/` with `status: superseded` + `superseded_by`. Move history, never rewrite it.
- **Escalate**: ambiguous conflict → leave in `inbox/`, flag in `log.md` for a human.
- **Demote**: knowledge unreferenced and `last_verified` > 180 days → `archive/` with `status: archived`.
- **Reindex**: regenerate maps (rung 1); rebuild `memory.db` if used. Append run summary to `log.md`.

Profile extension to core §6: **maintenance stages (numbered 90+) MAY write across the
workspace** instead of only `output/`. Numbering convention: 90+ = recurring maintenance.

---

## 5. Recall — the 3-rung ladder

Protocol is fixed; the substrate scales underneath it. Climb one rung only when the rung below fails.

| rung | mechanism                                        | good until    | added tooling |
|------|--------------------------------------------------|---------------|---------------|
| 1    | `index.md` maps (per-directory, generated)       | ~500 concepts | none |
| 2    | grep, or FTS: `python3 tools/psindex.py search "query"` | ~50k concepts | 1 stdlib script |
| 3    | semantic/vector index behind the same protocol   | beyond        | embeddings / external store |

**Law: files are the truth; every index is derived and disposable.**
`memory.db` can always be rebuilt (`psindex.py build`). If db and files disagree, files win.

---

## 6. Forget

- Default recall scope excludes `archive/` and any `status` ≠ `current`.
- Archiving is a **move, not a delete**: provenance stays greppable, supersession chains stay walkable.
- Recall quality depends on the size of the **active set**, not total size. Consolidation + archive keep the active set flat while total grows.

---

## 7. Reading protocol (agent)

1. Read `index.md`. Load the `# Core` block if present (it is the always-in-context memory).
2. Resolve the target from maps (rung 1); else search (rung 2). Open ONE file. Stop.
3. Trust frontmatter. Check `status` before acting on a fact. Follow `supersedes` chains only when auditing.

---

# Notes

Why an inbox: agents skip saving when saving is expensive. The single biggest failure
mode of file-based memory is an empty one. Capture is deliberately allowed to be messy;
consolidation pays the formatting cost later, in batch.

Why archive instead of delete: a memory that deletes cannot answer "why did we think X?"
Archiving keeps audits possible at zero hot-path cost, since recall excludes it by default.

Why the db is a cache: the moment the database becomes the truth, the workspace stops
being reviewable with `cat` and shippable with `git clone` — the two properties the whole
format exists to protect. Deriving it from frontmatter keeps both worlds.
