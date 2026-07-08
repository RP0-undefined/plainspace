# Changelog

Versioning: the spec version lives in the `SKILL.md` title. **Additive** change (new
optional field, profile, tool subcommand) → minor bump. **Breaking** change (a conformant
workspace stops being conformant, or a documented default changes meaning) → major bump.

## v0.3.1 — 2026-07-08

Link graph (Phase 10.1/10.3, from the DeusData/codebase-memory-mcp review) — additive
tooling; core spec unchanged. The MCP adapter (10.2) was declined (out of scope: Plainspace
is conventions, not a runtime).

- **Queryable link graph** in `memory.db` (`links` table): markdown links + frontmatter
  relations (`supersedes`/`derived_from`/`promoted_to`/`superseded_by`) + the `# Core`
  block; generated maps excluded. Stdlib only.
- **`psindex.py links <path>`**: "what references this / what does it reference", by kind,
  flagging broken targets.
- **`stats`** gains **demotion candidates** (unreferenced + provably >180d — finally
  operationalizes MEMORY §5's demotion rule) and **orphans** (no links in or out).

## v0.3 — 2026-07-08

Auto-capture (memory profile, Phase 9) — additive, no breaking changes.

- **Optional `89_extract` stage**: an out-of-band extractor turns harness-transcript turns
  into `inbox/` captures (`type: Capture`, `confidence: medium`), guaranteeing capture by
  mechanism instead of the advisory checkpoint. The extractor is an agent run driven by the
  stage contract — not a script. Numbered 89 so one sweep runs "89 then 90" (extract →
  consolidate).
- **State = a watermark, not a counter** (`.autocapture/watermark`): pending is derived
  (transcript lines past the watermark); idempotent and crash-safe.
- **`psindex.py`**: `stats` reads the watermark and flags `<- EXTRACT` when pending ≥
  threshold; new `watermark` subcommand advances it (stdlib only).
- Docs: MEMORY.md §4b, SETUP.md §3/§3b (per-harness adapter table), worked example
  `examples/memory-workspace/89_extract/`. Guard rails: out-of-band only, secrets guard,
  batch cap, never delete harness-native transcripts.

## v0.2.1 — 2026-07-07

Patch, surfaced by real production use of the memory profile.

- **Fix (bug 4)**: `psindex.py stats` used `(_days_ago(last_verified) or 10**6) > 180`, so a
  concept verified *today* (`days_ago == 0`, falsy) was misreported as maximally stale. Now
  `(d := _days_ago(...)) is None or d > 180` — missing still flags, today no longer does.
  Regression test added (`test_stats_today_not_stale`).
- **Spec clarification (MEMORY.md §5d, "mailbox rule")**: single-writer exclusivity applies
  only to consolidation and to `knowledge/`/`archive/`/`index.md`/`log.md` mutations;
  appending a uniquely-named capture to `inbox/` is always lock-free-safe from any session.

## v0.2 — 2026-07-06

Memory profile hardening (see `MEMORY.md`), no breaking changes to the core spec.

- **Traceability**: consolidated captures are archived to `archive/inbox/` with
  `promoted_to` (never deleted); promoted knowledge carries `derived_from`. Unbroken
  L3→L0 drill-down by frontmatter alone.
- **Named layer pyramid** (L0→L3) documented; `# Core` block gains a lifecycle
  (consolidation-regenerated, per-line links, ≤15-line budget).
- **Smarter consolidation**: warmup schedule + thresholds declared as stage frontmatter
  (`triggers:`); session-end trigger option in `SETUP.md`.
- **Recall budgets**: ≤5 candidates, open one, degrade gracefully; `psindex search` gains
  `--limit` (default 5) and `--since`.
- **Dedup** step at consolidation; scoring-with-decay design note in `design/`.
- **Tooling**: `psindex.py` rewritten (argparse; partial map regeneration preserving the
  `# Core` block; staleness auto-rebuild; body-aware LIKE fallback; `stats` provenance
  counter; new `check` conformance subcommand). Stdlib `unittest` suite + GitHub Actions CI.
- **Benchmark** (`bench/`) quantifying the load-less claim.
- Link style flipped to plain-relative (leading-`/` still tolerated on read).

## v0.1 — 2026-06-28

Initial release: core spec (`SKILL.md`), `BOOTSTRAP.md`, MIT license, generic worked
example. Later in the series: the Memory profile (`MEMORY.md`), `tools/psindex.py`,
`SETUP.md`, and the memory worked example.
