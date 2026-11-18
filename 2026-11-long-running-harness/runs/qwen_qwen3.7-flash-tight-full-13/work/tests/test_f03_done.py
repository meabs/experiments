"""Tests for feature F03: done command."""
import subprocess
import tempfile
import os
import unittest


class TestDone(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True
        )
        return result

    def test_done_marks_task(self):
        self._run("add", "Buy milk")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_done_shows_as_x(self):
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_fails(self):
        r = self._run("done", "99")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 99", r.stderr)


if __name__ == "__main__":
    unittest.main()
