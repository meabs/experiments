"""Tests for feature F05: priority."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


TASKS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


class TestF05Priority(unittest.TestCase):
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

    def test_add_priority_high_shows_suffix(self):
        out, err, rc = self._run("add", "a", "--priority", "high")
        self.assertEqual(rc, 0)
        out2, _, _ = self._run("list")
        self.assertIn("(high)", out2)

    def test_add_priority_low_shows_suffix(self):
        out, err, rc = self._run("add", "a", "--priority", "low")
        self.assertEqual(rc, 0)
        out2, _, _ = self._run("list")
        self.assertIn("(low)", out2)

    def test_add_priority_medium_no_suffix(self):
        out, err, rc = self._run("add", "a", "--priority", "medium")
        self.assertEqual(rc, 0)
        out2, _, _ = self._run("list")
        self.assertNotIn("(high)", out2)
        self.assertNotIn("(low)", out2)

    def test_default_priority_is_medium(self):
        out, err, rc = self._run("add", "a")
        self.assertEqual(rc, 0)
        out2, _, _ = self._run("list")
        self.assertNotIn("(high)", out2)
        self.assertNotIn("(low)", out2)

    def test_list_sort_priority_orders_high_medium_low(self):
        self._run("add", "C", "--priority", "low")
        self._run("add", "A", "--priority", "high")
        self._run("add", "B", "--priority", "medium")
        out, _, _ = self._run("list", "--sort", "priority")
        lines = out.split("\n")
        # High first, then medium, then low; ties by id
        self.assertTrue(lines[0].startswith("2 "))  # A high
        self.assertTrue(lines[1].startswith("3 "))  # B medium
        self.assertTrue(lines[2].startswith("1 "))  # C low

    def test_invalid_priority_exits_1(self):
        out, err, rc = self._run("add", "a", "--priority", "urgent")
        self.assertEqual(rc, 1)
        self.assertIn("Invalid priority: urgent", err)


if __name__ == "__main__":
    unittest.main()
