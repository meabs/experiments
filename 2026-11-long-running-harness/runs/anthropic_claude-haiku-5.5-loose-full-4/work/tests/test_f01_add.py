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


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_add_prints_ids_and_creates_file(self):
        r = run(self.d, "add", "Buy milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        self.assertTrue(os.path.exists(os.path.join(self.d, "tasks.json")))
        r = run(self.d, "add", "Walk dog")
        self.assertEqual(r.stdout.strip(), "Added 2")
        with open(os.path.join(self.d, "tasks.json")) as f:
            data = json.load(f)
        self.assertEqual([t["title"] for t in data["tasks"]], ["Buy milk", "Walk dog"])
        self.assertFalse(data["tasks"][0]["done"])


if __name__ == "__main__":
    unittest.main()
