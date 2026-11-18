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


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_add_prints_ids_and_creates_file(self):
        r = run(self.dir, "add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        r = run(self.dir, "add", "Walk dog")
        self.assertEqual(r.stdout.strip(), "Added 2")
        self.assertTrue(os.path.exists(os.path.join(self.dir, "tasks.json")))
        with open(os.path.join(self.dir, "tasks.json")) as f:
            data = json.load(f)
        self.assertEqual(data["tasks"][0]["title"], "Buy milk")
        self.assertFalse(data["tasks"][0]["done"])


if __name__ == "__main__":
    unittest.main()
