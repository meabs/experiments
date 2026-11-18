import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd, capture_output=True, text=True)


class TestTags(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_suffix_order(self):
        run(self.dir, "add", "a", "--tag", "work", "--tag", "home")
        run(self.dir, "add", "b", "--priority", "high", "--tag", "work")
        run(self.dir, "add", "c")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a #work #home", "2 [ ] b (high) #work", "3 [ ] c"])

    def test_filter(self):
        run(self.dir, "add", "a", "--tag", "work")
        run(self.dir, "add", "b", "--tag", "home")
        run(self.dir, "add", "c", "--tag", "work", "--tag", "home")
        r = run(self.dir, "list", "--tag", "work")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a #work", "3 [ ] c #work #home"])

    def test_old_tasks_without_tags(self):
        with open(os.path.join(self.dir, "tasks.json"), "w") as f:
            f.write('{"next_id": 2, "tasks": [{"id": 1, "title": "old", "done": false}]}')
        self.assertEqual(run(self.dir, "list").stdout.strip(), "1 [ ] old")


if __name__ == "__main__":
    unittest.main()
