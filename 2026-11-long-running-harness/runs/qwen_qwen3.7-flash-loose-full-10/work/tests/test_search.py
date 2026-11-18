import subprocess
import json
import os
import sys
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


def run(*args, cwd=None):
    """Run tasks.py with given args and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        [sys.executable, TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF09_Search(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_search_case_insensitive(self):
        """search milk matches 'Buy Milk'."""
        run('add', 'Buy Milk', cwd=self.tmpdir)
        out, err, rc = run('search', 'milk', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, '1 [ ] Buy Milk')

    def test_search_no_match(self):
        """No match prints 'No matches'."""
        run('add', 'Buy Milk', cwd=self.tmpdir)
        out, err, rc = run('search', 'xyz', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'No matches')

    def test_search_multiword_title(self):
        """search matches substring in multi-word title."""
        run('add', 'Buy milk and cookies', cwd=self.tmpdir)
        out, err, rc = run('search', 'milk and', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, '1 [ ] Buy milk and cookies')


if __name__ == '__main__':
    unittest.main()
