#!/usr/bin/env python3
"""Tests for tasks.py - Feature F06: tags."""

import os
import subprocess
import tempfile
import unittest


class TestTags(unittest.TestCase):
    """Test feature F06: tags."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        project_root = os.path.dirname(os.path.dirname(__file__))
        result = subprocess.run(
            ["python3", os.path.join(project_root, "tasks.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_with_tags(self):
        """add with --tag shows tag suffix."""
        r = self._run("add", "a", "--tag", "work", "--tag", "home")
        self.assertEqual(r.stdout.strip(), "Added 1")
        r2 = self._run("list")
        lines = r2.stdout.strip().split("\n")
        self.assertIn("#work #home", lines[0])

    def test_list_filter_by_tag(self):
        """list --tag filters tasks."""
        self._run("add", "a", "--tag", "work")
        self._run("add", "b", "--tag", "home")
        r = self._run("list", "--tag", "work")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("#work", lines[0])

    def test_tag_suffix_order(self):
        """Suffix order: priority then tags."""
        r = self._run("add", "a", "--priority", "high", "--tag", "work")
        r2 = self._run("list")
        line = r2.stdout.strip()
        # Should have (high) before #work
        self.assertIn("(high)", line)
        self.assertIn("#work", line)
        high_pos = line.index("(high)")
        tag_pos = line.index("#work")
        self.assertLess(high_pos, tag_pos)


if __name__ == "__main__":
    unittest.main()
