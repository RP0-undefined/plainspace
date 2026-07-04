---
type: Stage
audience: agent
stage: 90
title: Consolidate
description: Promote inbox captures into knowledge; supersede and archive; reindex.
inputs:
  - inbox/
  - log.md
outputs: []
updated: 2026-07-04T00:00:00Z
---

Maintenance stage (90+): writes across the workspace, not to output/.
One writer: never run two consolidations concurrently.

Process:
- If the workspace is a git repo: `git commit -am "memory: pre-consolidate"` (local only).
- For each file in inbox/: locate the matching concept in knowledge/ (grep key terms).
  - New fact → create or extend a concept. Carry source + confidence from the capture.
  - Contradicts an existing fact → newer wins unless its confidence is lower.
    Move the losing file/fact to archive/ with status: superseded + superseded_by.
  - Ambiguous → leave in inbox/, flag in log.md for a human.
- Delete consolidated inbox files.
- Demote: knowledge with last_verified older than 180 days and no inbound links → archive/, status: archived.
- Regenerate maps; rebuild memory.db if tools/psindex.py is used.
- Append a run summary to log.md with counters: promoted / superseded / archived /
  left-ambiguous (see tools/psindex.py stats).
- If git repo: `git commit -am "memory: consolidate <date> — <counters>"` (local only).
  The diff against pre-consolidate is the human review gate.
