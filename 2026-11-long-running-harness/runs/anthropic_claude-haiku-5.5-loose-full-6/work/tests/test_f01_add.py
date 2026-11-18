import json
import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd, capture_output=True, text=True)


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_add_prints_ids_and_creates_file(self):
        r = run(self.dir, "add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        self.assertTrue(os.path.exists(os.path.join(self.dir, "tasks.json")))
        r = run(self.dir, "add", "Walk dog")
        self.assertEqual(r.stdout.strip(), "Added 2")
        with open(os.path.join(self.dir, "tasks.json")) as f:
            data = json.load(f)
        self.assertEqual([t["title"] for t in data["tasks"]], ["Buy milk", "Walk dog"])
        self.assertFalse(data["tasks"][0]["done"])

    def test_add_without_title_is_error(self):
        r = run(self.dir, "add")
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
