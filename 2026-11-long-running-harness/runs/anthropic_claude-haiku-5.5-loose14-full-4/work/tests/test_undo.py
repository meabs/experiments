import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(os.path.dirname(HERE), "tasks.py")


class TestUndo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.dir.cleanup()

    def run_cmd(self, *args, ok=True):
        p = subprocess.run([sys.executable, TASKS, *args], cwd=self.dir.name,
                           capture_output=True, text=True)
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr)
        return p

    def lines(self, *args):
        return self.run_cmd(*args).stdout.splitlines()

    def test_nothing_to_undo(self):
        p = self.run_cmd("undo", ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("Nothing to undo", p.stderr)

    def test_undo_add_reuses_id(self):
        self.run_cmd("add", "a")
        self.assertEqual(self.lines("undo"), ["Undone"])
        self.assertEqual(self.lines("list"), ["No tasks"])
        self.assertEqual(self.lines("add", "b"), ["Added 1"])

    def test_undo_done_edit_delete_in_turn(self):
        self.run_cmd("add", "a")          # 1
        self.run_cmd("add", "b")          # 2
        self.run_cmd("done", "1")
        self.run_cmd("edit", "2", "--title", "B2")
        self.run_cmd("delete", "1")
        self.assertEqual(self.lines("list"), ["2 [ ] B2"])
        self.run_cmd("undo")
        self.assertEqual(self.lines("list"), ["1 [x] a", "2 [ ] B2"])
        self.run_cmd("undo")
        self.assertEqual(self.lines("list"), ["1 [x] a", "2 [ ] b"])
        self.run_cmd("undo")
        self.assertEqual(self.lines("list"), ["1 [ ] a", "2 [ ] b"])
        self.run_cmd("undo")
        self.assertEqual(self.lines("list"), ["1 [ ] a"])
        self.run_cmd("undo")
        self.assertEqual(self.lines("list"), ["No tasks"])
        p = self.run_cmd("undo", ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("Nothing to undo", p.stderr)

    def test_failed_commands_not_recorded(self):
        self.run_cmd("add", "a")
        self.run_cmd("done", "99", ok=False)
        self.run_cmd("edit", "99", "--title", "x", ok=False)
        self.run_cmd("add", "b", "--priority", "bogus", ok=False)
        self.run_cmd("undo")
        self.assertEqual(self.lines("list"), ["No tasks"])
        self.run_cmd("undo", ok=False)

    def test_undo_across_runs_keeps_next_id(self):
        self.run_cmd("add", "a")
        self.run_cmd("add", "b")
        self.run_cmd("delete", "2")
        self.run_cmd("undo")   # restores b with id 2 in a fresh process
        self.assertEqual(self.lines("list"), ["1 [ ] a", "2 [ ] b"])
        self.assertEqual(self.lines("add", "c"), ["Added 3"])


if __name__ == "__main__":
    unittest.main()
