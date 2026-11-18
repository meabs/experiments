"""Tests for feature F06: tags."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


class TestF06Tags(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        tf = os.path.join(self.tmpdir, "tasks.json")
        if os.path.exists(tf):
            os.remove(tf)

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, TASKS_PY] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def test_add_tags_shows_suffix(self):
        out, err, rc = self._run("add", "a", "--tag", "work", "--tag", "home")
        self.assertEqual(rc, 0)
        out2, _, _ = self._run("list")
        self.assertIn("#work #home", out2)

    def test_list_tag_filters(self):
        self._run("add", "a", "--tag", "work")
        self._run("add", "b", "--tag", "home")
        out, _, _ = self._run("list", "--tag", "work")
        lines = out.split("\n")
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("1 "))

    def test_list_tag_no_match(self):
        self._run("add", "a", "--tag", "work")
        out, _, _ = self._run("list", "--tag", "nonexistent")
        self.assertEqual(out, "No tasks")

    def test_suffix_order_priority_then_tags(self):
        out, err, rc = self._run("add", "a", "--priority", "high", "--tag", "work")
        self.assertEqual(rc, 0)
        out2, _, _ = self._run("list")
        # Priority suffix comes before tags suffix
        self.assertIn("(high) #work", out2)


if __name__ == "__main__":
    unittest.main()
