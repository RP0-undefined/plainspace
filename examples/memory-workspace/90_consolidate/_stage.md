---
type: Stage
audience: agent
stage: 90
title: Consolidate
description: Promote inbox captures into knowledge; dedup, supersede, archive; refresh Core; reindex.
inputs:
  - inbox/
  - log.md
outputs: []
triggers: {inbox_files: 10, oldest_days: 7, warmup: true}
updated: 2026-07-06T00:00:00Z
---

Maintenance stage (90+): writes across the workspace, not to output/.
One writer: never run two consolidations concurrently.

Process:
- If git repo: `git add -A && git commit -m "memory: pre-consolidate"` (local only).
  Use `add -A`, not `-am` — new captures/concepts are untracked and `-am` skips them.
- For each file in inbox/:
  - Dedup: search knowledge/ for the same fact (psindex search on key terms).
    Duplicate → merge into the existing concept: keep highest confidence, union source,
    refresh last_verified. Do not create a second concept.
  - New fact → create or extend a concept in knowledge/. Set derived_from to the capture
    path; carry source + confidence.
  - Contradicts an existing fact → newer wins unless its confidence is lower.
    Move the loser to archive/ with status: superseded + superseded_by.
  - Ambiguous → leave in inbox/, flag in log.md for a human.
- Archive each consolidated capture to archive/inbox/<file> with status: consolidated and
  promoted_to: <knowledge path(s)>. Never delete — the raw evidence is kept (traceability).
- Demote: knowledge with last_verified older than 180 days and no inbound links → archive/,
  status: archived.
- Core refresh: every ~50 promotions, or when a concept cited by # Core is superseded,
  regenerate the # Core block in index.md (above the map marker). Each line links to the
  concept it distills; keep Core ≤ ~15 lines.
- Regenerate maps (`psindex.py map`); rebuild memory.db if tools/psindex.py is used.
- Append a run summary to log.md: promoted / merged / superseded / archived / left-ambiguous
  (see tools/psindex.py stats).
- If git repo: `git add -A && git commit -m "memory: consolidate <date> — <counters>"`.
  The diff against pre-consolidate is the human review gate.
