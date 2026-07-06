---
type: Patterns
audience: both
title: Optional patterns
description: >
  Conventions an agent can follow unaided, beyond the core spec. Optional — none
  is required for conformance. Read only the pattern you need.
updated: 2026-07-06T00:00:00Z
---

# Optional patterns

Not rules. Each is a convention you opt into per workspace.

## 1. Stage-state offload (long-running stages)

Problem: a long stage accumulates raw tool logs, search dumps, and intermediate output in
context until the window is the bottleneck.

Pattern: **offload the raw, keep a symbolic map in context.**

- Write each bulky artifact to `output/refs/<node-id>.md` (raw dump, never re-read whole).
- Maintain `output/state.md`: a compact table the agent re-reads instead of the dumps.

```
| id  | step            | status | ref                    |
|-----|-----------------|--------|------------------------|
| n01 | fetch orders    | done   | refs/n01-orders.md     |
| n02 | classify        | wip    | refs/n02-classify.md   |
| n03 | draft summary   | todo   |                        |
```

- The agent reads `state.md` (small), and opens a `refs/<id>.md` only when it needs that
  node's raw detail. `node_id`s make every row greppable back to its raw text.
- A Mermaid graph in `state.md` is allowed when the flow is non-linear; the table is the
  minimum.

**Why this is not a cipher (it obeys the token principle, doesn't break it).** This is
rule 2 — *put truth in structure* — not rule 3 abuse. The `id`s are stable references, not
invented shorthand for words; the raw text they point to is full natural language, one
open away. You compress the *index*, never the *content*. Contrast a cipher, which encodes
the content itself and forces the model to decompress it while reasoning.

# Notes

This pattern drifts toward runtime/harness territory (when to offload is a context-pressure
decision). Keep it to what an agent can do unaided with files; leave trigger ratios to the
harness (see `SETUP.md`).
