#!/usr/bin/env python3
"""Test feature: priority --priority high|medium|low, suffix '(high)'/'(low)', list --sort priority"""
import subprocess
import os
import tempfile
import shutil
import unittest


class TestF05Priority(unittest.TestCase):
    """Test feature: priority --priority high|medium|low, suffix '(high)'/'(low)', list --sort priority"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy(src, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_with_priority_high(self):
        """add a --priority high; list shows '1 [ ] a (high)'"""
        r = self._run("add", "a", "--priority", "high")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] a (high)")

    def test_add_with_priority_low(self):
        """add a --priority low; list shows '1 [ ] a (low)'"""
        r = self._run("add", "a", "--priority", "low")
        self.assertEqual(r.returncode, 0)
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] a (low)")

    def test_medium_has_no_suffix(self):
        """default medium shows no suffix"""
        r = self._run("add", "a")
        self.assertEqual(r.returncode, 0)
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] a")

    def test_list_sort_priority(self):
        """list --sort priority orders high, medium, low, ties by id"""
        self._run("add", "c", "--priority", "low")
        self._run("add", "b", "--priority", "high")
        self._run("add", "a")  # medium default
        r = self._run("list", "--sort", "priority")
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertIn("(high)", lines[0])
        self.assertNotIn("(", lines[1])  # medium
        self.assertIn("(low)", lines[2])

    def test_invalid_priority(self):
        """add --priority urgent exits 1 with 'Invalid priority: urgent'"""
        r = self._run("add", "a", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)


if __name__ == "__main__":
    unittest.main()
