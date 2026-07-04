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

## 3. Schedule consolidation (the memory's heartbeat)

Consolidation only exists if something triggers it. Pick ONE, with the human's approval:

| your situation                     | action |
|------------------------------------|--------|
| harness has scheduled/cron agents  | schedule a daily/weekly run: "Run `90_consolidate/_stage.md` per its contract" |
| OS scheduler available (cron, Task Scheduler) | e.g. `0 7 * * * cd /path/to/workspace && <agent-cli> -p "Run 90_consolidate/_stage.md per its contract"` |
| neither                            | fallback rule, add to your always-loaded instructions: "At session start, if `inbox/` has ≥ 10 files or its oldest capture is > 7 days old, run the consolidation stage before other work." |

The fallback is weaker (advisory, like all instructions) — prefer a real scheduler.

---

# Notes

Why one-time and separate: setup instructions loaded on every skill trigger
would charge recurring tokens for non-recurring work. This file is read once,
acted on, then never reopened — the hook it installs is what persists.

Why ask-first: an agent silently editing harness config is how trust dies.
The human sees the exact diff before it lands.
