import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestTags(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_tag_suffix_in_order(self):
        run(self.dir, "add", "a", "--tag", "work", "--tag", "home")
        self.assertEqual(run(self.dir, "list").stdout, "1 [ ] a #work #home\n")

    def test_list_filter_by_tag(self):
        run(self.dir, "add", "a", "--tag", "work")
        run(self.dir, "add", "b", "--tag", "home")
        run(self.dir, "add", "c", "--tag", "work")
        r = run(self.dir, "list", "--tag", "work")
        self.assertEqual(r.stdout, "1 [ ] a #work\n3 [ ] c #work\n")

    def test_priority_then_tags(self):
        run(self.dir, "add", "a", "--priority", "low", "--tag", "t")
        self.assertEqual(run(self.dir, "list").stdout, "1 [ ] a (low) #t\n")


if __name__ == "__main__":
    unittest.main()
