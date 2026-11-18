import json
import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestExport(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_json_fields(self):
        run(self.dir, "add", "Buy milk", "--priority", "high", "--tag", "home", "--tag", "shop", "--due", "2026-03-01")
        run(self.dir, "add", "Walk dog")
        run(self.dir, "done", "2")
        r = run(self.dir, "export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data[0], {"id": 1, "title": "Buy milk", "done": False, "priority": "high",
                                   "tags": ["home", "shop"], "due": "2026-03-01"})
        self.assertEqual(data[1], {"id": 2, "title": "Walk dog", "done": True, "priority": "medium",
                                   "tags": [], "due": None})

    def test_json_empty(self):
        r = run(self.dir, "export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), [])

    def test_csv(self):
        run(self.dir, "add", "Buy milk", "--priority", "low", "--tag", "home", "--tag", "shop")
        run(self.dir, "add", "Walk dog", "--due", "2026-03-01")
        run(self.dir, "done", "2")
        r = run(self.dir, "export", "--format", "csv")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "id,title,done,priority,tags,due\n"
                                   "1,Buy milk,false,low,home;shop,\n"
                                   "2,Walk dog,true,medium,,2026-03-01\n")

    def test_csv_empty_store(self):
        r = run(self.dir, "export", "--format", "csv")
        self.assertEqual(r.stdout, "id,title,done,priority,tags,due\n")


if __name__ == "__main__":
    unittest.main()
