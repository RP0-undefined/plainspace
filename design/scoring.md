# Design note: per-fact scoring with decay (proposal)

Status: **proposal, not implemented.** Backlog item from AGENTS.md. Owner approved the
direction; this doc proposes the design before any code, per the plan's Phase 5.2.

## Problem

Supersession handles *contradicted* facts. It does nothing for a fact that is simply going
stale — never contradicted, never re-confirmed, slowly less trustworthy. Today `stats`
flags `last_verified > 180d`, a blunt binary. A graded signal would let consolidation
prioritize what to re-verify or demote.

## Score

```
score = w_conf * confidence           # high=1.0 medium=0.6 low=0.3
      + w_recency * exp(-age_days / H) # H ~ 90d half-life on last_verified
      + w_usage * log1p(recall_count)  # how often recall surfaced this fact
```

Weights and H are constants in the tool; no per-fact tuning. Below a threshold → the fact
enters an **audit queue** surfaced by `psindex.py stats` (alongside the existing hygiene
counters), for the consolidation stage to re-verify, refresh `last_verified`, or demote.

## The one hard rule (why this is a design note, not a quick add)

`recall_count` is **usage telemetry**. It MUST live ONLY in `memory.db` — the disposable,
derived, gitignored cache — and NEVER in a file's frontmatter. Reasons:

- Writing a counter to a file on every recall turns reads into writes: churn, git noise,
  and write-contention against the single-writer boundary (§5d of MEMORY.md).
- It would make `memory.db` no longer purely derivable from files — breaking the core law
  "files are the truth, the db is disposable". Deleting the db must stay safe.

Consequence: `recall_count` is **best-effort and resettable**. Deleting `memory.db` zeroes
usage; recency + confidence (both in files) still produce a valid score. That is acceptable
— usage is a tie-breaker, not ground truth.

## Open questions (resolve before implementing)

- Who increments `recall_count`? `search` would have to record hits — but `search` today is
  read-only and side-effect-free. Adding a write on search is a real change; maybe a
  separate `--record` flag, opt-in, so the default stays pure.
- Threshold as a declared trigger (like `inbox_files`) vs a tool constant.
- Does scoring reorder recall results, or only feed the audit queue? Proposal: **audit
  queue only** at first. Reordering recall by a mutable score risks non-reproducible search
  (violates "delete db, rebuild, identical results"). Keep recall deterministic.
