import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.py"))


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestExportStats(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_export_empty_json(self):
        self.assertEqual(json.loads(run(self.dir, "export", "--format", "json").stdout), [])

    def test_export_json(self):
        run(self.dir, "add", "a", "--tag", "x", "--tag", "y", "--due", "2026-03-01")
        run(self.dir, "add", "b")
        run(self.dir, "done", "2")
        out = json.loads(run(self.dir, "export", "--format", "json").stdout)
        self.assertEqual(out[0], {"id": 1, "title": "a", "done": False, "priority": "medium",
                                  "tags": ["x", "y"], "due": "2026-03-01"})
        self.assertEqual(out[1]["done"], True)
        self.assertIsNone(out[1]["due"])

    def test_export_csv(self):
        run(self.dir, "add", "a", "--tag", "x", "--tag", "y")
        run(self.dir, "add", "b", "--priority", "low")
        out = run(self.dir, "export", "--format", "csv").stdout
        rows = list(csv.reader(io.StringIO(out)))
        self.assertEqual(rows[0], ["id", "title", "done", "priority", "tags", "due"])
        self.assertEqual(rows[1], ["1", "a", "false", "medium", "x;y", ""])
        self.assertEqual(rows[2], ["2", "b", "false", "low", "", ""])

    def test_stats(self):
        self.assertEqual(run(self.dir, "stats").stdout.splitlines(),
                         ["open: 0", "done: 0", "total: 0"])
        run(self.dir, "add", "a")
        run(self.dir, "add", "b")
        run(self.dir, "add", "c")
        run(self.dir, "done", "1")
        run(self.dir, "delete", "2")
        self.assertEqual(run(self.dir, "stats").stdout.splitlines(),
                         ["open: 1", "done: 1", "total: 2"])


if __name__ == "__main__":
    unittest.main()
