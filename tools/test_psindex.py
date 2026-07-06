#!/usr/bin/env python3
"""Stdlib unittest suite for psindex. Run: python3 tools/test_psindex.py"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psindex  # noqa: E402


def write(root, rel, frontmatter, body=""):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    fm = "".join(f"{k}: {v}\n" for k, v in frontmatter.items())
    p.write_text(f"---\n{fm}---\n{body}")
    return p


def out(fn, *args, **kwargs):
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


class Frontmatter(unittest.TestCase):
    def test_none(self):
        meta, body = psindex.parse_frontmatter("no frontmatter here")
        self.assertEqual(meta, {})
        self.assertEqual(body, "no frontmatter here")

    def test_scalar_list_folded(self):
        text = ("---\ntype: Metric\ntitle: T\ntags: [a, b]\n"
                "description: >\n  one line\nderived_from:\n  - x.md\n  - y.md\n"
                "---\nbody")
        meta, body = psindex.parse_frontmatter(text)
        self.assertEqual(meta["type"], "Metric")
        self.assertEqual(meta["tags"], "a, b")
        self.assertEqual(meta["description"], "one line")
        self.assertEqual(meta["derived_from"], "x.md, y.md")
        self.assertEqual(body.strip(), "body")

    def test_unclosed(self):
        meta, _ = psindex.parse_frontmatter("---\ntype: X\nno close")
        self.assertEqual(meta, {})


class Workspace(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root, "knowledge/pricing.md",
              {"type": "Reference", "title": "Pricing", "status": "current",
               "source": "page", "last_verified": "2026-06-28"},
              "Team 29 EUR SSO roadmap")
        write(self.root, "archive/old.md",
              {"type": "Metric", "title": "Old", "status": "superseded",
               "superseded_by": "knowledge/pricing.md"}, "stale funnel")
        write(self.root, "inbox/2026-07-04-call.md",
              {"type": "Capture", "source": "call"}, "- zulu residency ask")

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_and_search_hides_archive(self):
        r = out(psindex.search, self.root, "pricing")
        self.assertIn("knowledge/pricing.md", r)
        r = out(psindex.search, self.root, "funnel")
        self.assertIn("no results", r)                 # archived hidden by default
        r = out(psindex.search, self.root, "funnel", show_all=True)
        self.assertIn("archive/old.md", r)

    def test_body_only_capture_findable(self):
        r = out(psindex.search, self.root, "zulu")     # word only in capture body
        self.assertIn("inbox/2026-07-04-call.md", r)

    def test_staleness_rebuild(self):
        out(psindex.build, self.root)
        write(self.root, "inbox/2026-07-05-x.md", {"type": "Capture"}, "- yankee fact")
        r = out(psindex.search, self.root, "yankee")   # must auto-rebuild
        self.assertIn("2026-07-05-x.md", r)

    def test_since_filter(self):
        r = out(psindex.search, self.root, "pricing", since="2027-01-01")
        self.assertIn("no results", r)

    def test_map_preserves_core(self):
        (self.root / "index.md").write_text(
            f"# Core\n* keep me\n\n{psindex.MARKER}\n# old\n")
        out(psindex.build_maps, self.root)
        txt = (self.root / "index.md").read_text()
        self.assertIn("# Core", txt)
        self.assertIn("keep me", txt)
        self.assertIn("Subdirectories", txt)           # regenerated below marker
        self.assertNotIn("# old", txt)

    def test_map_skips_handwritten_without_marker(self):
        (self.root / "knowledge" / "index.md").write_text("# hand written\n")
        out(psindex.build_maps, self.root)
        self.assertEqual((self.root / "knowledge" / "index.md").read_text(),
                         "# hand written\n")

    def test_stats_runs(self):
        r = out(psindex.stats, self.root)
        self.assertIn("inbox backlog: 1", r)
        self.assertIn("lacking provenance", r)

    def test_check_detects_broken_chain(self):
        write(self.root, "knowledge/bad.md",
              {"type": "Reference", "superseded_by": "knowledge/ghost.md"}, "x")
        problems = []
        buf = io.StringIO()
        with redirect_stdout(buf):
            problems = psindex.check(self.root)
        self.assertTrue(any("ghost.md" in p for p in problems))

    def test_check_detects_missing_type(self):
        (self.root / "knowledge" / "notype.md").write_text("---\ntitle: X\n---\nbody")
        with redirect_stdout(io.StringIO()):
            problems = psindex.check(self.root)
        self.assertTrue(any("notype.md" in p and "type" in p for p in problems))


if __name__ == "__main__":
    unittest.main(verbosity=2)
