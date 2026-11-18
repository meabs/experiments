import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestF02List(unittest.TestCase):
    """Feature F02: list prints one line per task in id order, or 'No tasks'"""

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

    def test_empty_list(self):
        """Empty list prints 'No tasks'"""
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_list_two_tasks(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'"""
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        r = self._run("list")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_with_done_task(self):
        """Done tasks show [x]"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        lines = r.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")


if __name__ == "__main__":
    unittest.main()
