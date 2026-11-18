import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF02List(unittest.TestCase):
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

    def test_empty_list(self):
        result = self._run("list")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "No tasks")

    def test_list_shows_tasks_in_order(self):
        self._run("add", "Buy milk")
        self._run("add", "Walk dog")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")


if __name__ == "__main__":
    unittest.main()
