---
type: Stage
audience: agent
stage: 2
title: Draft
description: Turn collected material into a draft following the style guide.
inputs:
  - 01_collect/output/raw.md       # product: this run's working artifact
  - knowledge/style-guide.md       # factory: stable reference
outputs:
  - draft.md
updated: 2026-01-01T00:00:00Z
---

Process:
- Read 01_collect/output/raw.md.
- Write draft.md in the voice from knowledge/style-guide.md. Save to output/.
- Use only facts present in raw.md. Do not invent.
