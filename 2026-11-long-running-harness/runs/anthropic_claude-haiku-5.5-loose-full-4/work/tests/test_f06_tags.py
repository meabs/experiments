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
        self.d = tempfile.mkdtemp()

    def test_tags_suffix(self):
        run(self.d, "add", "a", "--tag", "work", "--tag", "home")
        self.assertEqual(run(self.d, "list").stdout.splitlines(), ["1 [ ] a #work #home"])

    def test_list_filter_by_tag(self):
        run(self.d, "add", "a", "--tag", "work")
        run(self.d, "add", "b", "--tag", "home")
        run(self.d, "add", "c", "--tag", "work", "--tag", "home")
        self.assertEqual(run(self.d, "list", "--tag", "work").stdout.splitlines(),
                         ["1 [ ] a #work", "3 [ ] c #work #home"])

    def test_suffix_order_priority_then_tags(self):
        run(self.d, "add", "a", "--priority", "low", "--tag", "t")
        self.assertEqual(run(self.d, "list").stdout.splitlines(), ["1 [ ] a (low) #t"])


if __name__ == "__main__":
    unittest.main()
