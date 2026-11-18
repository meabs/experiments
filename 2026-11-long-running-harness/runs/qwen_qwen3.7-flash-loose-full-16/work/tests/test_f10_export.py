import os
import subprocess
import shutil
import tempfile
import unittest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(SCRIPT_DIR, "..", "tasks.py")


class TestF10Export(unittest.TestCase):
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

    def test_export_json_empty(self):
        result = self._run("export", "--format", "json")
        self.assertEqual(result.stdout.strip(), "[]")

    def test_export_json_with_tasks(self):
        self._run("add", "Task one", "--priority", "high", "--tag", "work", "--due", "2026-03-01")
        self._run("done", "1")
        result = self._run("export", "--format", "json")
        import json
        data = json.loads(result.stdout)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["title"], "Task one")
        self.assertTrue(data[0]["done"])
        self.assertEqual(data[0]["priority"], "high")
        self.assertEqual(data[0]["tags"], ["work"])
        self.assertEqual(data[0]["due"], "2026-03-01")

    def test_export_csv_empty(self):
        result = self._run("export", "--format", "csv")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertEqual(len(lines), 1)

    def test_export_csv_with_tasks(self):
        self._run("add", "Task one", "--priority", "low", "--tag", "home")
        self._run("add", "Task two")
        result = self._run("export", "--format", "csv")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "id,title,done,priority,tags,due")
        self.assertEqual(lines[1], "1,Task one,false,low,home,")
        self.assertEqual(lines[2], "2,Task two,false,medium,,")

    def test_export_csv_done_and_due(self):
        self._run("add", "Done task", "--due", "2026-01-01")
        self._run("done", "1")
        result = self._run("export", "--format", "csv")
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[1], "1,Done task,true,medium,,2026-01-01")

    def test_export_csv_tags_joined_with_semicolon(self):
        self._run("add", "Multi tag", "--tag", "a", "--tag", "b")
        result = self._run("export", "--format", "csv")
        lines = result.stdout.strip().split("\n")
        self.assertIn("a;b", lines[1])


if __name__ == "__main__":
    unittest.main()
