import unittest
import subprocess
import os
import json
import tempfile
import shutil


class TestF03Done(unittest.TestCase):
    """Feature F03: done - marks a task done, prints 'Done <id>'; unknown id -> stderr 'No such task: <id>', exit 1"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        src = os.path.join(self.original_cwd, "tasks.py")
        dst = os.path.join(self.test_dir, "tasks.py")
        shutil.copy(src, dst)
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.test_dir
        )
        return result

    def test_done_prints_id(self):
        """done 1 prints 'Done 1'"""
        self._run("add", "Buy milk")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")

    def test_list_shows_done_task(self):
        """After done, list shows '[x]' format"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("list")
        lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_unknown_id_exits_1(self):
        """done 9 exits 1 with 'No such task: 9'"""
        r = self._run("done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "No such task: 9")

    def test_unknown_id_stderr_only(self):
        """done on unknown id has no stdout"""
        r = self._run("done", "9")
        self.assertEqual(r.stdout.strip(), "")

    def test_already_done_still_works(self):
        """Marking an already-done task as done still succeeds"""
        self._run("add", "Buy milk")
        self._run("done", "1")
        r = self._run("done", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 1")


if __name__ == "__main__":
    unittest.main()
