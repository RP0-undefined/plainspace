# AGENTS.md — project handoff

Context for any AI coding agent resuming work on this repo (Claude Code, Codex,
or otherwise — `AGENTS.md` is the cross-tool standard). This file is about
*developing the repo*, not about using the format (that's `SKILL.md`).

## What this project is

**Plainspace** — a plain-text format that gives an AI agent durable knowledge and
multi-step workflows as a folder of markdown files. Conventions only: no
framework, no schema registry, no required tooling. Status: **v0.2, published**
(memory profile hardened; see `CHANGELOG.md`).

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
├── PATTERNS.md      # Optional conventions (stage-state offload). Not required for conformance.
├── BOOTSTRAP.md     # Paste-into-system-prompt snippet so any agent can read/write a workspace
├── AGENTS.md        # This handoff (dev context, agent-neutral name)
├── CHANGELOG.md  CONTRIBUTING.md  LICENSE   # v0.2; contribution bar; MIT © 2026 Dorunaitsu
├── tools/
│   ├── psindex.py       # rung 2: SQLite+FTS5 index, STDLIB ONLY (build/search/map/stats/check)
│   ├── pssearch3.py     # rung 3: hybrid BM25+embeddings (RRF); stdlib, optional /v1/embeddings backend
│   └── test_psindex.py  # stdlib unittest suite (run: python3 tools/test_psindex.py)
├── bench/           # reproducible token benchmark (naive vs index-first vs FTS)
├── design/scoring.md  # design note (proposal, not implemented): per-fact scoring with decay
├── .github/workflows/ci.yml  # tests + conformance on examples
└── examples/
    ├── sample-workspace/   # Complete generic worked example (collect -> draft pipeline + knowledge base)
    └── memory-workspace/   # Memory profile: # Core (per-line links) + generated maps, inbox/,
        #                     knowledge/ (derived_from/source/status), archive/inbox/ (promoted_to),
        #                     90_consolidate/_stage.md (triggers: frontmatter)
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
8. **Memory v0.2 laws (added; do not undo).** (g) Unbroken traceability: consolidated
   captures are archived (`archive/inbox/` + `promoted_to`), never deleted; promoted
   knowledge carries `derived_from`. An agent can drill L3→L0 by frontmatter alone.
   (h) `# Core` is a generated layer with a ≤15-line budget and per-line links — it is
   the only always-loaded file, so it must be the most disciplined. (i) Recall is
   deterministic and budgeted (≤5, open one, degrade gracefully); usage telemetry (if
   ever added, see `design/scoring.md`) lives ONLY in the disposable db, never in files.
   (j) `pssearch3.py` (rung 3) is a substrate swap behind the same verb; without an
   embeddings backend it falls back to FTS. Deleting the db and rebuilding must reproduce
   results.
9. **Rejected from TencentDB-Agent-Memory (source of the v0.2 review).** Borrowed its
   *concepts* (pyramid, traceability, budgets, hybrid recall), never its storage model:
   NO database as source of truth for lower layers; NO gateway/HTTP service, plugin, auth,
   or Docker; NO required embeddings or non-stdlib dependency in the core path; captures
   stay markdown, not a JSONL atom store.
10. **Auto-capture laws (v0.3 Phase 9, do not undo).** (a) Extraction is OUT-OF-BAND only
    (scheduler/session-end) — never mid-conversation (no latency/cost/context pollution).
    (b) State is a **watermark, not a counter** — pending is derived (lines since watermark);
    idempotent, crash-safe (write captures → advance watermark). (c) The extractor writes
    `inbox/` ONLY (mailbox-safe); it never touches `knowledge/` and never consolidates.
    (d) Auto facts default `confidence: medium` (deliberate captures may claim `high`);
    hard secrets guard (never extract credentials); batch cap ≤~20. (e) Never delete a
    harness-native transcript store; only adapter-owned logs, only past the watermark.
    (f) The extractor is an agent run driven by `89_extract/_stage.md` — NOT a script;
    `psindex.py` only reads the watermark (`stats`) and advances it (`watermark`).

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
- [x] **Memory v0.2** (2026-07-06): traceability, named pyramid, Core lifecycle+budget,
      warmup/declared triggers, recall budgets, dedup, `psindex check`, tests + CI,
      `bench/`, `CHANGELOG.md`, `CONTRIBUTING.md`, spec-version policy, rung-3
      `pssearch3.py`, `PATTERNS.md`. Spec bumped v0.1 → v0.2.
- [x] **v0.2.1** (2026-07-07): bug 4 fix (`stats` falsy-zero) + regression test;
      MEMORY.md §5d "mailbox rule" clarification.
- [x] **v0.3 — Phase 9 auto-capture** (2026-07-08): optional `89_extract` stage (the
      extractor is an agent run driven by its contract, not a script); watermark over a
      harness transcript source; `psindex.py stats` `<- EXTRACT` flag + `watermark`
      subcommand (stdlib); MEMORY.md §4b, SETUP.md §3/§3b adapter table, worked example.
- [x] **v0.3.1 — Phase 10.1/10.3 link graph** (2026-07-08): `links` table in the db,
      `psindex.py links <path>`, `stats` demotion-candidate + orphan counters
      (operationalizes the demotion rule). Phase 10.2 (MCP adapter) DECLINED — out of scope
      (conventions, not a runtime).
- [ ] Optional backlog: implement `design/scoring.md` after resolving its open questions
      (owner approval); propose Plainspace as an optional skill to
      NousResearch/hermes-agent (issue-first — draft written, owner action);
      second non-memory example (research-to-brief pipeline).
