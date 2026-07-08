---
type: Stage
audience: agent
stage: 89
title: Extract (auto-capture)
description: Out-of-band extractor — turn durable facts from the harness transcript into inbox/ captures.
inputs:
  - .capture_log/          # transcript source (adapter-owned here; a real harness may point source_glob elsewhere)
  - .autocapture/watermark  # last processed position
outputs: []
source_glob: .capture_log/*.jsonl
triggers: {extract_turns: 5, oldest_hours: 24}
updated: 2026-07-06T00:00:00Z
---

Optional stage. Runs OUT-OF-BAND only (scheduler/session-end), never mid-conversation.
It writes to inbox/ only — it never touches knowledge/ and never consolidates
(single-writer stays with 90_consolidate). inbox appends are mailbox-safe (MEMORY §5d).

Trigger: `psindex.py stats` shows `<- EXTRACT` when pending turns (lines in `source_glob`
past `.autocapture/watermark`) ≥ `extract_turns`. One scheduled sweep runs "89 then 90".

Process:
- Read transcript lines in source_glob AFTER the watermark (`.autocapture/watermark`).
- Extract durable facts only: decisions, constraints, preferences, outcomes, config, errors.
  Skip chit-chat and anything transient.
- **Secrets guard:** NEVER extract credentials, API keys, tokens, or pasted `.env` content.
- Dedup within this batch; write at most ~20 capture files to inbox/ as
  `inbox/<date>-<slug>.md` — frontmatter `type: Capture`, `source: auto-extract <session> <date>`,
  `confidence: medium` (only deliberate in-session captures may claim `high`). One fact per line.
- Leftover turns beyond the batch cap stay pending (watermark advances only past processed lines).
- Advance the watermark AFTER writing captures (crash-safe order): `python3 tools/psindex.py watermark .`
- Do NOT delete a harness-native transcript store (e.g. Claude Code's ~/.claude/projects/).
  Only an adapter-owned log may be pruned, and only past the watermark.

# Notes
<!-- human-only -->
source_glob here is workspace-local (`.capture_log/*.jsonl`) so the example is self-contained.
A Claude Code deployment sets it to `~/.claude/projects/<project-slug>/*.jsonl` (no hook needed);
a Hermes deployment to `~/.capture_log/*.jsonl` fed by a post_llm_call plugin. See SETUP.md §3b.
No sample transcript is committed — transcripts are ephemeral and may contain secrets.
