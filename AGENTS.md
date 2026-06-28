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
├── BOOTSTRAP.md     # Paste-into-system-prompt snippet so any agent can read/write a workspace
├── AGENTS.md        # This handoff (dev context, agent-neutral name)
├── LICENSE          # MIT © 2026 Dorunaitsu
└── examples/sample-workspace/   # Complete generic worked example (collect -> draft pipeline + knowledge base)
    ├── index.md  log.md
    ├── knowledge/{style-guide.md (audience: both), glossary.md (audience: agent)}
    ├── 01_collect/{_stage.md, output/.gitkeep}
    └── 02_draft/{_stage.md, output/.gitkeep}
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
- [ ] **Publish:** create the GitHub repo and push (owner action;
      `gh repo create plainspace --public --source=. --remote=origin --push`).
- [ ] Optional backlog: a tiny no-dependency conformance checker script;
      a second example (e.g. a research-to-brief pipeline); `CONTRIBUTING.md`;
      a one-line spec-version bump policy.
