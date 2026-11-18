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


class TestTags(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_tags_suffix_in_order(self):
        run(self.dir, "add", "a", "--tag", "work", "--tag", "home")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a #work #home"])

    def test_priority_then_tags_suffix(self):
        run(self.dir, "add", "a", "--priority", "low", "--tag", "t")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a (low) #t"])

    def test_list_filter_by_tag(self):
        run(self.dir, "add", "a", "--tag", "work")
        run(self.dir, "add", "b", "--tag", "home")
        run(self.dir, "add", "c", "--tag", "work", "--tag", "home")
        r = run(self.dir, "list", "--tag", "work")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a #work", "3 [ ] c #work #home"])

    def test_list_filter_no_match(self):
        run(self.dir, "add", "a", "--tag", "work")
        self.assertEqual(run(self.dir, "list", "--tag", "x").stdout.strip(), "No tasks")


if __name__ == "__main__":
    unittest.main()
