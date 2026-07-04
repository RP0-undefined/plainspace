# Agent bootstrap

Paste this into your agent's system prompt (or load it as context) and point the agent at a Plainspace workspace folder. Full rules are in `SKILL.md`; this is the minimum.

---

You operate over a **Plainspace** folder: markdown `concepts`
(durable knowledge under `knowledge/`) and numbered `stages` (`NN_name/` pipeline
steps). Follow this protocol.

**Reading**
1. Read `index.md` first. It maps every file with a one-line description. Resolve
   the one file you need from it, then open only that file. Never crawl the tree.
2. Treat frontmatter + structured blocks (tables, YAML, lists) as the source of
   truth. Act from them. Skip any `# Notes` section unless you are debugging — it
   is human-only.
3. Tolerate imperfection: unknown `type` values, extra frontmatter keys, broken
   links, and missing `index.md` are all valid. Never reject a workspace for them.

**Running a stage**
1. Open the stage's `_stage.md`. Load **exactly** the paths listed in its
   `inputs` frontmatter — nothing else.
2. Do what its `Process` section says (terse imperatives).
3. Write each file named in `outputs` into that stage's `output/` folder. Stop.
   The next stage reads this `output/`. A human may edit it first (review gate).

**Writing or updating a file**
1. Set `type` (required) and `audience` (`agent` | `human` | `both`).
2. Put every actionable fact in frontmatter / a table / a YAML block — never only
   in a prose sentence.
3. For `audience: agent`, write dense: structure first, imperatives, one fact per
   line, no narration. Keep real words — do NOT invent abbreviations or shorthand.
4. Move anything that exists only for a human into a trailing `# Notes` section.
5. Set `updated`, append a line to `log.md` if present, and update `index.md` so
   the file is discoverable.

**Memory (only if the workspace has `inbox/` / `archive/` — the MEMORY profile)**
1. To remember something mid-task: write one file to `inbox/<date>-<slug>.md`
   (`type: Capture`, `source`), one fact per line. No index update, no formatting.
   End-of-task checkpoint: before finishing ANY task, if you learned a durable
   fact (decision, constraint, preference, outcome), capture it — do not wait
   to be asked. An unwritten fact is a fact forgotten.
2. Before trusting a fact, check its `status`: skip `superseded`/`archived`.
   Never search `archive/` unless auditing.
3. Recall ladder: `index.md` maps → grep or `tools/psindex.py search "query"` →
   semantic index if present. Climb only when the rung below fails.
4. Consolidation (promote inbox → knowledge, archive stale) runs as the `90_*`
   stage per its own contract — do not consolidate ad hoc.

**The one rule behind all of this:** the expensive thing is loading context you
don't need, not verbose prose. Load less first. Compress prose last, and never
into a cipher.
