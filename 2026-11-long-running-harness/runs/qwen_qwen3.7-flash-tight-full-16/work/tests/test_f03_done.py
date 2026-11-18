"""Feature F03: done ID marks done, prints 'Done <id>'; unknown id -> stderr 'No such task: <id>', exit 1"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestF03Done(unittest.TestCase):
    """Feature F03: done command"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), "..", "tasks.py")
        shutil.copy(src, os.path.join(self.tmpdir, "tasks.py"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, "tasks.py"] + list(args),
            capture_output=True, text=True,
            cwd=self.tmpdir
        )
        return result

    def test_done_prints_done_id(self):
        """done 2 prints 'Done 2'"""
        self._run("add", "Buy milk")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_list_shows_done_task(self):
        """list shows '1 [x] ...' after done"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        """done 9 exits 1 with 'No such task: 9'"""
        self._run("add", "Buy milk")
        r = self._run("done", "99")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 99")

    def test_done_twice(self):
        """Marking an already done task as done again should work (set done=True again)"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")


if __name__ == "__main__":
    unittest.main()
