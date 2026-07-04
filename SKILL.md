---
name: plainspace
description: >
  Read and write a self-hosted knowledge + workflow filesystem for an AI agent —
  markdown "concepts" (durable knowledge) and numbered "stages" (multi-step
  pipelines), written for agent consumption first and human review second. Use
  this whenever the agent must store, retrieve, or update durable knowledge; run
  or define a multi-step workflow whose stages live as folders; build a reference
  corpus it can traverse cheaply; or write/edit any .md it will itself read later.
  Use it even when the user only says "remember this", "save it for later",
  "set up a workflow", "make a knowledge base", or "note that down" — this format
  still applies. Prefer it over free-form note files. Also invoke it PROACTIVELY,
  without being asked: before finishing any task in which you learned a durable
  fact (a decision, constraint, preference, or outcome), capture it to the
  workspace — an unwritten fact is a fact forgotten.
---

# Plainspace v0.1

A merge of two existing ideas plus one addition.

- **OKF** (Open Knowledge Format): knowledge = a folder of markdown + YAML frontmatter, self-describing, git-shippable.
- **ICM** (Interpretable Context Methodology): workflow = numbered stage folders, each loading only the context it needs.
- **Addition**: files are authored for the **agent** first. An agent must be able to act from frontmatter + structured blocks alone, without reading prose that exists only for a human. Human explanation is *segregated*, not deleted.

Stance: plain text, no tooling, no schema registry, git-friendly. If you can `cat` it you can read it; if you can `git clone` it you can ship it.

---

## 1. The token principle — read this first

The expensive thing is **not** verbose prose. It is **loading content you do not need**, and **forcing the model to decompress a cipher**. Optimize in this order; earlier items dominate later ones:

1. **Load less.** Read `index.md` (the map) first, then jump straight to the one file — or one section — you need. Never crawl the tree. Never load a stage's whole reference set when its contract declares one file.
2. **Put truth in structure.** Every machine-actionable fact lives in frontmatter, a YAML/JSON block, or a table — never *only* in a prose sentence. You can then act by reading structured blocks and skipping prose entirely.
3. **Only then, compress prose.** Drop narration, transitions, hedging, restated headings, "as we can see". Keep **real words and explicit references**. Terse natural language — not a cipher.

**Hard limit on compression:** do NOT invent abbreviations, drop articles into ambiguity, or encode facts in shorthand. The model parses natural-ish structured language cheaply; it parses invented shorthand expensively (it spends reasoning tokens decompressing, and accuracy drops). You save input tokens and lose output quality — a bad trade. The real win in step 3 is deleting *redundant narration*, not deleting *language*.

**Never** strip a file so far a human cannot review it. Review/observability is the whole point of this format. Human-only explanation is moved, not removed (see §4).

---

## 2. Workspace layout

A workspace is one folder. Two kinds of content live in it.

```
workspace/
├── index.md                 # MAP. Read first. Lists every concept + stage with one-line desc + path.
├── log.md                   # Optional. Change history, newest first.
│
├── knowledge/               # CONCEPTS — durable, stable across runs (this is ICM "Layer 3 / factory").
│   ├── <concept>.md
│   └── <subdir>/<concept>.md
│
├── 01_<stage>/              # STAGES — a pipeline step. Numbering = execution order.
│   ├── _stage.md            #   Contract: what it reads / does / writes (see §6).
│   └── output/              #   Working artifacts for THIS run (ICM "Layer 4 / product").
├── 02_<stage>/
│   ├── _stage.md
│   └── output/
└── ...
```

- **Knowledge-only** use (a reference corpus, no pipeline): just `index.md` + `knowledge/`. Skip the numbered folders.
- **Workflow** use: numbered stages. Each stage's `output/` is the next stage's input.
- A workspace ships as a git repo (preferred), a zip, or a subfolder of a bigger repo.

---

## 3. Frontmatter

YAML block delimited by `---` at the very top of every concept and stage file. This block is the **canonical, agent-actionable surface** of the file.

| field         | required | applies to    | meaning |
|---------------|----------|---------------|---------|
| `type`        | **yes**  | all           | Short self-describing kind: `Reference`, `Playbook`, `Stage`, `Supplier`, `API`, `Metric`, … Not registered anywhere. Consumers MUST tolerate unknown types. |
| `audience`    | rec.     | all           | `agent` \| `human` \| `both` (default `both`). See §4. |
| `title`       | rec.     | all           | Display name. |
| `description` | rec.     | all           | One line. Used in `index.md` and previews. |
| `updated`     | rec.     | all           | ISO 8601 datetime of last meaningful change. |
| `tags`        | opt.     | all           | YAML list, cross-cutting categories. |
| `resource`    | opt.     | concepts      | Canonical URI of the asset the concept describes (omit for abstract concepts). |
| `stage`       | stage    | stages        | Integer execution order (matches folder prefix). |
| `inputs`      | stage    | stages        | YAML list of paths this stage loads. The agent loads exactly these — nothing else. |
| `outputs`     | stage    | stages        | YAML list of files this stage writes (to `output/`). |

Producers MAY add any other keys. Consumers MUST preserve unknown keys and MUST NOT reject a file for unknown fields.

---

## 4. `audience` — the agent-only layer

`audience` tells you how to read a file and how to write one.

| value    | how to WRITE the body                                                   | how to READ the body |
|----------|------------------------------------------------------------------------|----------------------|
| `agent`  | Dense. Structure first (tables, key:value, lists). Imperatives. One fact per line. No narration. | Trust frontmatter + structured blocks as truth. |
| `human`  | Explanatory prose, for a person reviewing.                              | Read fully only when a human asked, or when debugging. |
| `both`   | Structured truth at top; optional short prose below.                    | Read top-down; stop once you have what you need. |

**Segregation rule (the key mechanism).** Content that exists *only* for human comprehension goes at the **bottom**, under a reserved heading:

```
# Notes
<!-- human-only. Consuming agents skip this section unless debugging. -->
```

So a file's normal read path is: frontmatter → structured body → stop. The `# Notes` prose costs zero context on the hot path, but a human (or you, when debugging) can still scroll to it. You get density *and* reviewability instead of trading one for the other.

**Density discipline for `audience: agent` bodies:**
- Lead with structure. A table or `key: value` list beats a paragraph.
- One fact per line — diffable and retrievable.
- Imperatives for instructions: `Fetch orders. Filter status=paid. Write to output/.` — not "This stage will fetch the orders and then…".
- No transitions, no hedging, no restating the heading, no meta ("It's worth noting…").
- Resolve references explicitly: write the path or ID, never "the file mentioned above".
- Keep real words. Density comes from *cutting narration*, not from cutting grammar.

---

## 5. `index.md` — the map (biggest token saver)

One per workspace root (and optionally per subdirectory). No frontmatter. It lets you find the right file without opening any others — this is what makes "load less" possible.

```
# Knowledge
* [Kavrosa suppliers](knowledge/kavrosa-suppliers.md) — direct producers, terms, contacts
* [Server stack](knowledge/server-stack.md) — hosts, ports, services

# Workflow
* [01 collect](01_collect/_stage.md) — pull raw source into output/
* [02 draft](02_draft/_stage.md) — turn collected material into a draft
```

**Always read `index.md` first.** Resolve the target from it, open that one file, act, stop.
You MAY regenerate `index.md` by scanning frontmatter (`title`/`description`) when it is stale or missing.

---

## 6. Stage contracts

Each numbered stage holds one `_stage.md`. The contract lives in **frontmatter** (so you load inputs without parsing prose); the body holds only the terse process.

```
---
type: Stage
audience: agent
stage: 2
title: Draft
description: Turn collected material into a draft.
inputs:
  - 01_collect/output/         # Layer 4: this run's working artifacts
  - knowledge/voice.md         # Layer 3: stable reference
outputs:
  - draft.md
updated: 2026-06-28T00:00:00Z
---

Process:
- Read every file in 01_collect/output/.
- Write draft.md following knowledge/voice.md. Save to output/.
- Do not invent facts absent from inputs.
```

**Loading protocol for a workflow run:**
1. Read the stage's frontmatter. Load **exactly** the paths in `inputs` — nothing else.
2. Execute `Process` (imperatives).
3. Write each file in `outputs` to this stage's `output/`.
4. Stop. The next stage reads this `output/`. A human may edit `output/` before it runs (review gate).

This is the filesystem doing a framework's job: sequencing = folder numbers; scoping = `inputs`; state = files on disk; handoff = one stage's `output/` is the next's input.

**Re-run cheaply (incremental):** if a later stage needs rework but its inputs are unchanged, re-run only that stage. Changing a `knowledge/` file invalidates only the stages that list it in `inputs`.

---

## 7. Cross-links & citations

- Link concept→concept with markdown links. Bundle-relative (leading `/`) is preferred: `[suppliers](/knowledge/kavrosa-suppliers.md)`.
- A link asserts a relationship; its *kind* is conveyed by the surrounding line, not the link. Consumers MUST tolerate broken links (target may be not-yet-written knowledge).
- Sources backing a claim go under a trailing `# Citations` list, numbered. Keep them in `# Notes` if they are human-only.

---

## 8. Consumption rules (be permissive)

When reading any workspace:
- Treat frontmatter + structured blocks as the source of truth.
- Skip `# Notes` unless a human asked or you are debugging.
- Do **not** reject a file/workspace for: missing optional fields, unknown `type`, unknown extra keys, broken links, or a missing `index.md`.
- A workspace is *conformant* if every non-reserved `.md` has parseable frontmatter with a non-empty `type`. Everything else is soft guidance.

---

## 9. Writing checklist (when YOU create or update a file)

1. Pick `type`. Set `audience` (`agent` for anything only you will consume).
2. Put every actionable fact in frontmatter / a table / a YAML block.
3. Write the body dense: structure first, imperatives, one fact per line, no narration.
4. Move any human-only explanation to a trailing `# Notes` section.
5. Set `updated`. Add a line to `log.md` if the workspace keeps one.
6. Update `index.md` (or regenerate it) so the new file is discoverable.

---

## 10. Example

A minimal worked workspace is in `examples/sample-workspace/` — two knowledge concepts (one `audience: agent`, one `both`), two stages with frontmatter contracts, an `index.md`, and a `log.md`. Read `examples/sample-workspace/index.md` first, as the protocol prescribes.

---

## 11. Profiles

Optional extensions layered on this core; core rules remain law. One exists today:

- **Memory** (`MEMORY.md`) — long-term agent memory: cheap capture (`inbox/`), a recurring consolidation stage (90+), supersession fields, `archive/` forgetting, and a 3-rung recall ladder (maps → grep/FTS → semantic) so agent behavior survives scale. Worked example: `examples/memory-workspace/`.
