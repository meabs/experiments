import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.py"))


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestExport(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_empty_json(self):
        r = run(self.dir, "export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), [])

    def test_json_fields(self):
        run(self.dir, "add", "a", "--priority", "high", "--tag", "work", "--tag", "home",
            "--due", "2026-03-01")
        run(self.dir, "add", "b")
        run(self.dir, "done", "2")
        r = run(self.dir, "export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), [
            {"id": 1, "title": "a", "done": False, "priority": "high",
             "tags": ["work", "home"], "due": "2026-03-01"},
            {"id": 2, "title": "b", "done": True, "priority": "medium",
             "tags": [], "due": None},
        ])

    def test_csv(self):
        run(self.dir, "add", "a", "--priority", "low", "--tag", "work", "--tag", "home",
            "--due", "2026-03-01")
        run(self.dir, "add", "b")
        run(self.dir, "done", "2")
        r = run(self.dir, "export", "--format", "csv")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines(), [
            "id,title,done,priority,tags,due",
            "1,a,false,low,work;home,2026-03-01",
            "2,b,true,medium,,",
        ])

    def test_csv_empty_store_header_only(self):
        r = run(self.dir, "export", "--format", "csv")
        self.assertEqual(r.stdout.splitlines(), ["id,title,done,priority,tags,due"])


if __name__ == "__main__":
    unittest.main()
