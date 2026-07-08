---
type: Setup
audience: agent
title: Workspace setup (one-time, agent-executable)
description: >
  Read ONCE when first adopting a workspace: optionally make the memory
  checkpoint deterministic by configuring your own harness. Never reload
  this file on the hot path.
updated: 2026-07-04T00:00:00Z
---

# One-time setup

You (the agent) execute this yourself when you first operate over a Plainspace
workspace. Everything here is optional — the workspace works with zero setup.

Tiers (do in order of need): **§1 checkpoint** = L1, set it up first · **§2 tooling / §3
scheduling** = L2, add when the workspace grows.

**Rules:**
- ASK the human before modifying any harness or system config. Show the exact change first.
- Apply the step for YOUR harness only. Skip the rest.
- When done: confirm to the human what was configured; append one line to `log.md`.

---

## 1. Make the memory checkpoint deterministic

Skill descriptions and instructions are advisory — models under-trigger them.
A harness-level hook injects the reminder mechanically. Reminder text to inject:

> Memory checkpoint: before finishing, capture durable facts
> (decision, constraint, preference, outcome) to inbox/.

| your harness              | mechanism                                    | action |
|---------------------------|----------------------------------------------|--------|
| Claude Code               | hooks in `.claude/settings.json`             | add the `UserPromptSubmit` hook below |
| other, with hook support  | equivalent event that injects context        | inject the reminder text on each turn or on session end |
| no hook support           | always-loaded instruction file (`AGENTS.md`, system prompt, custom instructions) | append the reminder text there |

Claude Code example (project `.claude/settings.json`):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command",
        "command": "echo '[memory] Checkpoint: before finishing, capture durable facts (decision, constraint, preference, outcome) to inbox/.'" } ] }
    ]
  }
}
```

Cost: ~15 tokens per turn, deterministic. Verify your harness's current hook
schema in its docs before writing — schemas change.

---

## 2. Verify rung-2 tooling (optional)

- Run `python3 tools/psindex.py build .` once. If it succeeds, rung 2 of the
  recall ladder is available. If python3 is missing, skip — rung 1 (maps + grep)
  needs nothing.

---

## 3. Schedule the heartbeat (consolidation, + auto-capture if set up)

The heartbeat only exists if something triggers it. If the auto-capture stage
`89_extract/` is present (§3b below), the scheduled prompt is **"Run `89_extract/_stage.md`
then `90_consolidate/_stage.md` per their contracts"** (extract fresh facts, then
consolidate). Without it, just run `90_consolidate`. Pick ONE, with the human's approval:

| your situation                     | action |
|------------------------------------|--------|
| harness has scheduled/cron agents  | schedule a daily/weekly run of the heartbeat prompt above |
| harness supports subagents         | delegate the heartbeat run to a dedicated subagent — the `_stage.md` files are the complete prompt. Do NOT delegate capture or targeted recall: they belong to the calling agent |
| harness has a session-end hook     | on session end, run `psindex.py stats`; if it flags `<- EXTRACT` or `<- CONSOLIDATE`, trigger the heartbeat (the idle-timeout equivalent) |
| OS scheduler available (cron, Task Scheduler) | e.g. `0 7 * * * cd /path/to/ws && <agent-cli> -p "Run 89_extract then 90_consolidate per their contracts"` |
| neither                            | fallback rule in your always-loaded instructions: "At session start, run `psindex.py stats`; if it flags `<- EXTRACT`/`<- CONSOLIDATE`, run the heartbeat before other work." |

Thresholds are declared on the stages (`triggers:` frontmatter) and read by `psindex.py stats`
— don't hardcode them in the hook. The fallback is weaker (advisory) — prefer a real scheduler.

### 3b. Auto-capture adapters (optional, Phase 9)
Auto-capture guarantees `inbox/` fills without relying on the advisory checkpoint (§1). It
needs a transcript source; wire the one for your harness, then add `89_extract/` (see the
worked example). The extractor is an agent run driven by `89_extract/_stage.md` — no script.

| harness | transcript source (`source_glob` on `89_extract`) | note |
|---------|----------------------------------------------------|------|
| Claude Code | `~/.claude/projects/<project-slug>/*.jsonl` (native session logs) | **no hook needed**; never delete these — the watermark tracks progress |
| Hermes | a `post_llm_call` plugin appends `{ts,session,user,assistant}` to `~/.capture_log/*.jsonl` | adapter-owned log; delete lines only after the watermark passes them |
| any hook-capable | a turn-end hook appends the same JSONL | as above |
| no hooks / no transcripts | auto-capture unavailable — the §1 advisory checkpoint is the fallback | — |

Optional, if your harness exposes context-window usage: trigger the stage-state offload
pattern (`PATTERNS.md` §1) at ~50% window and force it by ~85%. This is harness business,
not part of the spec.

---

# Notes

Why one-time and separate: setup instructions loaded on every skill trigger
would charge recurring tokens for non-recurring work. This file is read once,
acted on, then never reopened — the hook it installs is what persists.

Why ask-first: an agent silently editing harness config is how trust dies.
The human sees the exact diff before it lands.
