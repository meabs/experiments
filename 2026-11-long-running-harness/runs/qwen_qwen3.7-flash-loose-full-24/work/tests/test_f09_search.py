#!/usr/bin/env python3
"""Test feature: search TEXT case-insensitive substring on title"""
import subprocess
import os
import tempfile
import shutil
import unittest


class TestF09Search(unittest.TestCase):
    """Test feature: search TEXT: case-insensitive substring on title, same line format, or 'No matches'"""

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

    def test_search_matches_case_insensitive(self):
        """search milk matches 'Buy Milk' and 'milkshake'"""
        self._run("add", "Buy Milk")
        self._run("add", "Make milkshake")
        r = self._run("search", "milk")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertIn("1 [ ] Buy Milk", lines)
        self.assertIn("2 [ ] Make milkshake", lines)

    def test_search_no_match(self):
        """no match prints 'No matches'"""
        self._run("add", "Buy milk")
        r = self._run("search", "xyz")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No matches")

    def test_search_exact_word(self):
        """search for exact word works"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("search", "buy")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] Buy milk")

    def test_search_in_id_order(self):
        """results are in id order"""
        self._run("add", "Buy apples")
        self._run("add", "Buy oranges")
        self._run("add", "Buy bananas")
        r = self._run("search", "buy")
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] Buy apples")
        self.assertEqual(lines[1], "2 [ ] Buy oranges")
        self.assertEqual(lines[2], "3 [ ] Buy bananas")

    def test_search_with_priority_suffix(self):
        """search results include priority suffix"""
        self._run("add", "Work task", "--priority", "high")
        self._run("add", "Other task")
        r = self._run("search", "work")
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] Work task (high)")


if __name__ == "__main__":
    unittest.main()
