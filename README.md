# Plainspace

A plain-text format for giving an AI agent **durable knowledge** and **multi-step workflows** as a folder of markdown files — readable by humans, but written for agents first.

No framework. No schema registry. No required tooling. If you can `cat` a file you can read it; if you can `git clone` a repo you can ship it.

Plainspace merges two prior ideas and adds one:

- **Knowledge as files** — from the [Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md): a directory of markdown + YAML frontmatter, self-describing, permissive to consume.
- **Workflows as folders** — from [Interpretable Context Methodology (ICM)](https://arxiv.org/abs/2603.16021): numbered stage folders, each loading only the context it needs, with a human review gate between stages.
- **Agent-first authoring** (the addition) — every machine-actionable fact lives in structured form so an agent can act from frontmatter + tables alone, while human-only explanation is *segregated* (not deleted) so you can still review and debug.

> Not the same thing as [`AGENTS.md`](https://agents.md). That standard tells a coding agent how to behave *in a repo* (build, test, conventions). Plainspace is the agent's **knowledge + workflow store** — a different concern. The two compose fine: keep your `AGENTS.md` at the repo root, keep your Plainspace workspace in a folder.

## Why

Most "agent-readable" markdown is really written for humans: narration, transitions, restating. An agent pays tokens to read all of it. Plainspace flips the default — the agent reads `frontmatter → structured blocks → stop`, and anything that exists only for a person sits at the bottom under a `# Notes` heading the agent skips. You keep observability; the agent stops paying for it on the hot path.

But note the trap Plainspace is built to avoid: **the biggest token cost is loading what you don't need, not verbosity.** So the format's first rule is *load less* (read the map, open one file), and it explicitly forbids compressing prose into a cipher — LLMs decompress invented shorthand at the cost of reasoning and accuracy. Density here means *cutting narration*, not *cutting language*.

## What's in here

```
plainspace/
├── SKILL.md                       # The format spec + the protocol an agent follows.
├── BOOTSTRAP.md                   # Drop-in bootstrap to point any agent at a workspace.
├── LICENSE                        # MIT.
├── README.md
└── examples/
    └── sample-workspace/          # A complete, generic worked example.
        ├── index.md               #   the map — read first
        ├── log.md
        ├── knowledge/             #   concepts (durable knowledge / "factory")
        │   ├── style-guide.md     #     audience: both
        │   └── glossary.md        #     audience: agent
        ├── 01_collect/            #   a pipeline stage
        │   ├── _stage.md          #     contract: inputs / process / outputs
        │   └── output/            #     per-run artifacts ("product")
        └── 02_draft/
            ├── _stage.md
            └── output/
```

## Quickstart

1. Read [`SKILL.md`](SKILL.md) — it's the whole spec, ~1 page, and it practices what it preaches.
2. Open [`examples/sample-workspace/index.md`](examples/sample-workspace/index.md) and follow the links. That's exactly how an agent traverses it.
3. Copy `examples/sample-workspace/` somewhere and start editing. Replace the example concepts and stages with your own.

## Use it with your agent

Plainspace is conventions, not code, so it works with any agent that can read files — Claude, GPT, an open-weight model, an n8n/LangChain pipeline, whatever.

- **In a skill-aware system** (e.g. Claude): drop `SKILL.md` in as a skill. It triggers on knowledge/workflow tasks.
- **Anywhere else**: paste the contents of [`BOOTSTRAP.md`](BOOTSTRAP.md) into your agent's system prompt and point it at the workspace folder.

## Adapt it to your structure

The format is minimally opinionated. To fit your domain you only need to:

- Invent your own `type` values (`Supplier`, `API`, `Runbook`, `Customer`…). They aren't registered anywhere; consumers tolerate unknown ones.
- Organize `knowledge/` however your domain wants — subfolders are free.
- Add as many numbered stages as your workflow has, or drop the stages entirely if you only need a knowledge base.
- Add any extra frontmatter fields you like; conformant consumers preserve unknown keys.

A workspace is *conformant* if every non-reserved `.md` has parseable frontmatter with a non-empty `type`. Everything else is soft guidance.

## Attribution & license

Plainspace is an independent synthesis. It builds on the **ideas** of OKF (Apache-2.0, Google Cloud) and ICM (MIT, Van Clief & McDermott) without copying their text. Credit to both.

This project is released under the [MIT License](LICENSE) © 2026 Dorunaitsu. Fork it, rename the format, change the conventions — keep the notice and that's the only ask.
