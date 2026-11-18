"""Tests for Feature F03: done command."""
import os
import shutil
import subprocess
import tempfile
import unittest


class TestDone(unittest.TestCase):
    """Test cases for the 'done' command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy("tasks.py", self.tmpdir)
        self.tasks_json = os.path.join(self.tmpdir, "tasks.json")

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_done_prints_done_id(self):
        """done 2 prints 'Done 2'"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("done", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 2")

    def test_list_shows_done_with_x(self):
        """list shows '2 [x] Walk dog' after done"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("done", "2")
        r = self._run("list")
        self.assertIn("2 [x] Walk dog", r.stdout)

    def test_done_unknown_id_exits_1(self):
        """done 9 exits 1 with 'No such task: 9'"""
        r = self._run("done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)

    def test_done_already_done_still_works(self):
        """Calling done twice on same task works (idempotent-ish)"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_open_tasks_remain_open(self):
        """Undone tasks remain open [ ]"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        self._run("done", "2")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [x] Walk dog")


if __name__ == "__main__":
    unittest.main()
