# Benchmark

`bench.py` measures the core claim — *load less* — with numbers instead of an argument.

It generates a deterministic synthetic knowledge base (40 concepts + a map), then answers
the same 40 questions three ways, reporting tokens loaded and retrieval accuracy:

| strategy | what the agent loads |
|----------|----------------------|
| naive tree-crawl | every file in the workspace |
| index-first | `index.md`, resolve to one file, open it |
| rung-2 FTS | `psindex search` (≤5 candidate lines), open the top hit |

Run:

```
python3 bench/bench.py
```

Representative result (40 docs, tokens ≈ chars/4):

| strategy | avg tokens/query | accuracy |
|----------|------------------|----------|
| naive tree-crawl | 1876 | 100% |
| index-first | 644 | 100% |
| rung-2 FTS | 73 | 100% |

## Reading it honestly

- **Same answer, ~26× fewer tokens** (FTS vs crawl) on this corpus, and the ratio *grows*
  with corpus size: crawl scales O(total), index-first O(map), FTS O(query). That gap is
  the whole point of the format.
- Accuracy is 100% here because the synthetic facts are unambiguous — this benchmark
  isolates the **token** axis, not retrieval quality on messy data. Don't read it as a
  quality claim.
- Tokens are approximated as `chars/4` (no tokenizer dependency) so the run is reproducible
  anywhere. Absolute numbers are indicative; the *ratios* are the signal.
