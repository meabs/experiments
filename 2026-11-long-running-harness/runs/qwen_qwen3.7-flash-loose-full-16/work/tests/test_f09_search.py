import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF09Search(unittest.TestCase):
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

    def test_search_matches_case_insensitive(self):
        self._run("add", "Buy Milk")
        self._run("add", "milkshake")
        result = self._run("search", "milk")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("1 [ ] Buy Milk", lines[0])
        self.assertIn("2 [ ] milkshake", lines[1])

    def test_search_no_match(self):
        self._run("add", "Buy Milk")
        result = self._run("search", "xyz")
        self.assertEqual(result.stdout.strip(), "No matches")

    def test_search_with_tags_and_priority(self):
        self._run("add", "Work task", "--priority", "high", "--tag", "work")
        result = self._run("search", "work")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [ ] Work task (high) #work")

    def test_search_multiple_words(self):
        self._run("add", "Buy fresh milk")
        result = self._run("search", "fresh milk")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("Buy fresh milk", lines[0])


if __name__ == "__main__":
    unittest.main()
