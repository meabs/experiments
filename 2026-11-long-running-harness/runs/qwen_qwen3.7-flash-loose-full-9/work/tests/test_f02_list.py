import os
import subprocess
import tempfile
import shutil
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_tasks(args, cwd=None):
    result = subprocess.run(
        ["python3", TASKS_PY] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result


class TestF02List(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_empty_list_prints_no_tasks(self):
        """Empty list prints 'No tasks'"""
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "No tasks")

    def test_list_shows_tasks_in_id_order(self):
        """After two adds, lines are '1 [ ] Buy milk' and '2 [ ] Walk dog'"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["add", "Walk dog"], cwd=self.tmpdir)
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 [ ] Buy milk")
        self.assertEqual(lines[1], "2 [ ] Walk dog")

    def test_list_with_done_task(self):
        """List shows done tasks with [x]"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["done", "1"], cwd=self.tmpdir)
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_list_after_delete(self):
        """Delete removes task from list"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["add", "Walk dog"], cwd=self.tmpdir)
        run_tasks(["delete", "2"], cwd=self.tmpdir)
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "1 [ ] Buy milk")


if __name__ == "__main__":
    unittest.main()
