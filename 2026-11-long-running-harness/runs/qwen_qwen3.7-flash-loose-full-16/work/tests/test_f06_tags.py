import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF06Tags(unittest.TestCase):
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

    def test_add_with_tags_shows_suffix(self):
        self._run("add", "Task a", "--tag", "work", "--tag", "home")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Task a #work #home")

    def test_list_filters_by_tag(self):
        self._run("add", "Work task", "--tag", "work")
        self._run("add", "Home task", "--tag", "home")
        result = self._run("list", "--tag", "work")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("#work", lines[0])

    def test_priority_before_tags_in_format(self):
        self._run("add", "Task x", "--priority", "high", "--tag", "work")
        result = self._run("list")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Task x (high) #work")


if __name__ == "__main__":
    unittest.main()
