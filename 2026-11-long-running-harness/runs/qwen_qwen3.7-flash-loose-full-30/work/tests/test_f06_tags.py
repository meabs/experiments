import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


def run_task_manager(args, cwd=None):
    """Run tasks.py with given args and return (returncode, stdout, stderr)."""
    src = os.path.join(os.path.dirname(__file__), "..", "tasks.py")
    dst = os.path.join(cwd, "tasks.py") if cwd else "tasks.py"
    # Only copy if not already there
    if not os.path.exists(dst):
        shutil.copy(src, dst)
    cmd = [sys.executable, "tasks.py"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestF06Tags(unittest.TestCase):
    """Feature 06: tags - --tag repeatable, suffix '#work #home', list --tag work filters"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_add_with_tags_shows_suffix(self):
        """add a --tag work --tag home; list shows '1 [ ] a #work #home'"""
        rc, out, err = run_task_manager(["add", "a", "--tag", "work", "--tag", "home"], cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(out, "1 [ ] a #work #home")

    def test_list_tag_filter(self):
        """list --tag work shows only matching tasks"""
        run_task_manager(["add", "task1", "--tag", "work", "--tag", "home"], cwd=self.tmpdir)
        run_task_manager(["add", "task2", "--tag", "work"], cwd=self.tmpdir)
        run_task_manager(["add", "task3", "--tag", "home"], cwd=self.tmpdir)
        rc, out, err = run_task_manager(["list", "--tag", "work"], cwd=self.tmpdir)
        lines = out.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("task1", lines[0])
        self.assertIn("task2", lines[1])

    def test_suffix_order_priority_then_tags(self):
        """suffix order: priority then tags"""
        rc, out, err = run_task_manager(
            ["add", "a", "--priority", "high", "--tag", "work"], cwd=self.tmpdir
        )
        self.assertEqual(rc, 0)
        rc, out, err = run_task_manager(["list"], cwd=self.tmpdir)
        self.assertEqual(out, "1 [ ] a (high) #work")


if __name__ == "__main__":
    unittest.main()
