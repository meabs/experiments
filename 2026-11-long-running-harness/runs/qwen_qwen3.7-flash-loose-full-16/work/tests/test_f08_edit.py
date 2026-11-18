import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF08Edit(unittest.TestCase):
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

    def test_edit_replaces_title(self):
        self._run("add", "Old title")
        result = self._run("edit", "1", "--title", "New title")
        self.assertEqual(result.stdout.strip(), "Edited 1")

    def test_list_shows_new_title(self):
        self._run("add", "Old title")
        self._run("edit", "1", "--title", "New title")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] New title")

    def test_edit_unknown_id_exits_1(self):
        result = self._run("edit", "99", "--title", "Nope")
        self.assertEqual(result.returncode, 1)
        self.assertIn("No such task: 99", result.stderr)


if __name__ == "__main__":
    unittest.main()
