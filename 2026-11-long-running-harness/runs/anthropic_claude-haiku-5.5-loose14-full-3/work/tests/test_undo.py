import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.py")


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestUndo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_nothing_to_undo(self):
        r = run(self.dir, "undo")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Nothing to undo", r.stderr)

    def test_undo_add_reuses_id(self):
        run(self.dir, "add", "a")
        r = run(self.dir, "undo")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "Undone\n")
        self.assertEqual(run(self.dir, "list").stdout, "No tasks\n")
        self.assertEqual(run(self.dir, "add", "b").stdout, "Added 1\n")

    def test_undo_done_edit_delete_in_turn(self):
        run(self.dir, "add", "a")          # 1
        run(self.dir, "done", "1")
        run(self.dir, "edit", "1", "--title", "renamed")
        run(self.dir, "delete", "1")
        self.assertEqual(run(self.dir, "list").stdout, "No tasks\n")
        run(self.dir, "undo")              # restore 1 with edited title
        self.assertEqual(run(self.dir, "list").stdout, "1 [x] renamed\n")
        run(self.dir, "undo")              # undo edit
        self.assertEqual(run(self.dir, "list").stdout, "1 [x] a\n")
        run(self.dir, "undo")              # undo done
        self.assertEqual(run(self.dir, "list").stdout, "1 [ ] a\n")
        run(self.dir, "undo")              # undo add
        self.assertEqual(run(self.dir, "list").stdout, "No tasks\n")
        r = run(self.dir, "undo")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Nothing to undo", r.stderr)

    def test_failed_commands_not_recorded(self):
        run(self.dir, "add", "a")
        run(self.dir, "done", "9")         # fails, must not be recorded
        run(self.dir, "add", "--priority", "bogus", "x")
        run(self.dir, "undo")              # undoes add a
        self.assertEqual(run(self.dir, "list").stdout, "No tasks\n")
        self.assertEqual(run(self.dir, "undo").returncode, 1)

    def test_undo_across_runs(self):
        run(self.dir, "add", "a")
        run(self.dir, "add", "b")
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "list").stdout, "1 [ ] a\n")


if __name__ == "__main__":
    unittest.main()
