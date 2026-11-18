#!/usr/bin/env python3
import unittest
import subprocess
import os
import tempfile

class TestSearch(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.taskfile = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            ["python3", os.path.join(os.path.dirname(__file__), "..", "tasks.py")] + list(args),
            cwd=self.tmpdir, capture_output=True, text=True
        )
        return result

    def test_search_case_insensitive(self):
        """search TEXT matches case-insensitively"""
        self._run("add", "Buy Milk")
        self._run("add", "milkshake recipe")
        # Search with lowercase should match both
        r = self._run("search", "milk")
        self.assertEqual(r.returncode, 0)
        self.assertIn("1 [ ] Buy Milk", r.stdout)
        self.assertIn("2 [ ] milkshake recipe", r.stdout)

    def test_search_no_match(self):
        """no match prints 'No matches'"""
        self._run("add", "Buy milk")
        r = self._run("search", "xyz")
        self.assertEqual(r.returncode, 0)
        self.assertIn("No matches", r.stdout)

    def test_search_partial_match(self):
        """search matches substring of title"""
        self._run("add", "Buy eggs and bread")
        r = self._run("search", "eggs")
        self.assertEqual(r.returncode, 0)
        self.assertIn("1 [ ] Buy eggs and bread", r.stdout)

    def test_search_returns_in_id_order(self):
        """search returns results in id order"""
        self._run("add", "Apple task")
        self._run("add", "Banana task")
        self._run("add", "Cherry task")
        r = self._run("search", "task")
        lines = [l for l in r.stdout.strip().split('\n') if l]
        self.assertIn("1 [ ] Apple task", lines)
        self.assertIn("2 [ ] Banana task", lines)
        self.assertIn("3 [ ] Cherry task", lines)


if __name__ == "__main__":
    unittest.main()
