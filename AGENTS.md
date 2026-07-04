# AGENTS.md — project handoff

Context for any AI coding agent resuming work on this repo (Claude Code, Codex,
or otherwise — `AGENTS.md` is the cross-tool standard). This file is about
*developing the repo*, not about using the format (that's `SKILL.md`).

## What this project is

**Plainspace** — a plain-text format that gives an AI agent durable knowledge and
multi-step workflows as a folder of markdown files. Conventions only: no
framework, no schema registry, no required tooling. Status: **v0.1, complete,
ready to publish.**

It is a synthesis of three ideas:
- **OKF** (Open Knowledge Format, Google Cloud) — knowledge as markdown + YAML frontmatter.
- **ICM** (Interpretable Context Methodology, arXiv 2603.16021) — workflows as numbered stage folders.
- **Agent-first authoring** (the original addition) — files written for agent consumption first, human review second.

Source links live in `README.md` only (deliberately kept out of `SKILL.md` to
save consumer-agent tokens).

## Repo structure

```
plainspace/
├── README.md        # GitHub front page: what/why, attribution + source links, quickstart, adapt, license
├── SKILL.md         # THE SPEC. The format + the protocol an agent follows. Self-demonstrating (dense).
├── MEMORY.md        # PROFILE: long-term memory (capture→consolidate→recall→forget). Optional, layered on core.
├── SETUP.md         # One-time agent-executable setup: self-configure harness hooks (ask-first, never hot-path)
├── BOOTSTRAP.md     # Paste-into-system-prompt snippet so any agent can read/write a workspace
├── AGENTS.md        # This handoff (dev context, agent-neutral name)
├── LICENSE          # MIT © 2026 Dorunaitsu
├── tools/psindex.py # Optional derived index: SQLite+FTS5, stdlib only (build / search / map)
└── examples/
    ├── sample-workspace/   # Complete generic worked example (collect -> draft pipeline + knowledge base)
    │   ├── index.md  log.md
    │   ├── knowledge/{style-guide.md (audience: both), glossary.md (audience: agent)}
    │   ├── 01_collect/{_stage.md, output/.gitkeep}
    │   └── 02_draft/{_stage.md, output/.gitkeep}
    └── memory-workspace/   # Worked example of the Memory profile
        ├── index.md ("# Core" always-loaded block)  log.md
        ├── inbox/ (cheap capture)  knowledge/ (status/source/confidence/supersedes)
        ├── archive/ (superseded — excluded from recall)
        └── 90_consolidate/_stage.md (recurring maintenance stage)
```

## Design decisions — do not silently undo these

1. **The token principle (core).** Optimize in this order: (1) load less — read
   `index.md`, open only the file you need; (2) put truth in structure
   (frontmatter/tables/YAML); (3) compress prose last. **Never** compress into a
   cipher — invented shorthand makes models spend reasoning tokens decompressing
   and lowers accuracy. Density = cutting narration, not cutting language.
2. **Segregation, not deletion.** Human-only text goes in a trailing `# Notes`
   section the agent skips by default. Keeps observability without paying tokens
   on the hot path. The `audience: agent|human|both` frontmatter field drives this.
3. **Naming.** "AWF" was rejected — already taken in the agent space (GitHub's
   Agent Workflow Firewall, awf-project/cli, an Antigravity framework). Do not
   reintroduce it. Renamed to **Plainspace** (plain text + workspace).
4. **Agent-neutral naming, no gatekeeping.** The format is for *any* agent and
   *any* inference provider (Claude, Codex, Hermes, OpenClaw, open-weight, …) — do
   not phrase docs as if Claude were required. Two naming consequences:
   `AGENTS.md` (Linux Foundation standard for telling a coding agent how to
   behave *in a repo*) is this dev handoff; the *consumer-agent* bootstrap is
   named `BOOTSTRAP.md` to avoid colliding with it. Name specific agents only as
   examples, never as requirements.
5. **Examples stay generic.** An earlier draft was personalized (a user's server
   stack, suppliers). It was deliberately replaced with neutral content. Keep
   examples domain-neutral — no personal/real data.
6. **License: MIT, holder "Dorunaitsu".** Briefly trialed The Unlicense
   (public domain) then reverted to MIT by request.
7. **Memory profile laws (MEMORY.md).** (a) Files are the truth; every index
   (`memory.db`, generated `index.md` maps) is derived and disposable — if they
   disagree, files win. (b) Recall is a fixed 3-rung ladder (maps → grep/FTS →
   semantic); the protocol never changes, only the substrate under it. (c) Capture
   must be zero-ceremony (`inbox/`, no index update) or agents stop saving.
   (d) Forgetting = move to `archive/` + `status`, never delete — recall excludes
   archive by default. (e) Maintenance stages (90+) may write across the
   workspace, unlike regular stages. (f) `tools/psindex.py` stays stdlib-only and
   optional — the profile must work with zero tooling at small scale.

## Editing conventions

- `SKILL.md` must keep practicing what it preaches: dense, structure-first,
  imperative, ~under 500 lines. If you add rules, add them tersely.
- Don't add source/citation links to `SKILL.md` — README only.
- Keep `index.md` of the example in sync if you add/rename example files.
- A workspace is *conformant* if every non-reserved `.md` has parseable
  frontmatter with a non-empty `type`. Don't add hard validation beyond that.

## Status & next steps

- [x] Spec, bootstrap, generic example, README, license — done.
- [x] Local git repo initialized and committed (`Plainspace v0.1`).
- [x] **Published:** https://github.com/RP0-undefined/plainspace (public, `main`).
- [x] **Memory profile** (`MEMORY.md`) + `tools/psindex.py` + `examples/memory-workspace/`.
- [ ] Optional backlog: a tiny no-dependency conformance checker script;
      `CONTRIBUTING.md`; a one-line spec-version bump policy; rung-3 semantic
      recall reference implementation (embeddings behind the same search verbs);
      propose Plainspace as an optional skill to NousResearch/hermes-agent
      (issue-first — draft written, owner action).
