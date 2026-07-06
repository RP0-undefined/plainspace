# Contributing

Plainspace is conventions, not a framework. Contributions are welcome; the bar is that a
change must not betray the format's reasons for existing.

## Non-negotiables

- **Files are the truth.** Any index or database (`memory.db`, generated `index.md` maps)
  is derived and disposable — deleting it must be safe, rebuilding must reproduce it. Never
  make a database the source of truth for anything.
- **No required tooling.** The core spec works with `cat` + `grep`. `tools/psindex.py`
  stays **stdlib-only**. Anything needing dependencies (e.g. embeddings) is a separate,
  optional script that degrades gracefully when absent.
- **Agent- and provider-agnostic.** No gateway, server, plugin, or auth layer. Name
  specific agents only as examples, never as requirements.
- **Token discipline applies to the spec itself.** `SKILL.md` stays dense, structure-first,
  under ~500 lines. Density = cutting narration, never cutting language into a cipher.
- Respect `AGENTS.md` → "Design decisions — do not silently undo these".

## Workflow

1. Keep changes small and focused. Discuss larger direction in an issue first.
2. Run the checks locally before opening a PR:
   ```
   python3 tools/test_psindex.py
   python3 tools/psindex.py check examples/sample-workspace
   python3 tools/psindex.py check examples/memory-workspace
   ```
3. If you touch example files, regenerate their maps (`python3 tools/psindex.py map <ws>`)
   and keep them in sync.
4. Update `CHANGELOG.md` and bump the spec version in `SKILL.md` if the change is
   spec-visible (additive = minor, breaking = major).

## License

By contributing you agree your contribution is released under the repository's MIT license.
