import json
import os
import subprocess
import tempfile
import shutil
import unittest


TASKS_PY = os.path.join(os.path.dirname(__file__), "..", "tasks.py")


def run_tasks(args, cwd=None):
    """Run tasks.py with given args in a temp directory."""
    result = subprocess.run(
        ["python3", TASKS_PY] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result


class TestF03Done(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_done_prints_done_id(self):
        """done ID marks done, prints 'Done <id>'"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        result = run_tasks(["done", "1"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Done 1")

    def test_done_marks_task_as_done_in_list(self):
        """list shows '2 [x] ...' after done"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["done", "1"], cwd=self.tmpdir)
        result = run_tasks(["list"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[0], "1 [x] Buy milk")

    def test_done_unknown_id_exits_1(self):
        """done 9 exits 1 with 'No such task: 9' to stderr"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        result = run_tasks(["done", "99"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 1)
        self.assertIn("No such task: 99", result.stderr)

    def test_done_updates_json(self):
        """tasks.json has done=true after done command"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["done", "1"], cwd=self.tmpdir)
        with open(os.path.join(self.tmpdir, "tasks.json")) as f:
            data = json.load(f)
        self.assertTrue(data["tasks"]["1"]["done"])

    def test_done_on_already_done(self):
        """done on already done task still works"""
        run_tasks(["add", "Buy milk"], cwd=self.tmpdir)
        run_tasks(["done", "1"], cwd=self.tmpdir)
        result = run_tasks(["done", "1"], cwd=self.tmpdir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Done 1")


if __name__ == "__main__":
    unittest.main()
