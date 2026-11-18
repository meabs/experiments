import unittest
import tempfile
import json

from test_add import run


class TestExport(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_empty_json(self):
        r = run(self.dir, "export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), [])

    def test_json_fields(self):
        run(self.dir, "add", "Buy milk", "--priority", "high", "--tag", "home", "--tag", "x", "--due", "2024-01-02")
        run(self.dir, "add", "Walk")
        run(self.dir, "done", "2")
        r = run(self.dir, "export", "--format", "json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), [
            {"id": 1, "title": "Buy milk", "done": False, "priority": "high",
             "tags": ["home", "x"], "due": "2024-01-02"},
            {"id": 2, "title": "Walk", "done": True, "priority": "medium",
             "tags": [], "due": None},
        ])

    def test_csv(self):
        run(self.dir, "add", "Buy milk", "--priority", "low", "--tag", "home", "--tag", "x")
        run(self.dir, "add", "Walk", "--due", "2024-05-06")
        run(self.dir, "done", "2")
        r = run(self.dir, "export", "--format", "csv")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines(), [
            "id,title,done,priority,tags,due",
            "1,Buy milk,false,low,home;x,",
            "2,Walk,true,medium,,2024-05-06",
        ])

    def test_bad_format(self):
        r = run(self.dir, "export", "--format", "xml")
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
