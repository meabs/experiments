import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF03Done(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, os.path.join(self.dir, "tasks.py"))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            cwd=self.dir,
            capture_output=True, text=True
        )
        return result

    def test_done_marks_task(self):
        self._run("add", "Buy milk")
        result = self._run("done", "1")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Done 1")

    def test_done_shows_x_in_list(self):
        self._run("add", "Buy milk")
        self._run("done", "1")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        result = self._run("done", "99")
        self.assertEqual(result.returncode, 1)
        self.assertIn("No such task: 99", result.stderr)


if __name__ == "__main__":
    unittest.main()
