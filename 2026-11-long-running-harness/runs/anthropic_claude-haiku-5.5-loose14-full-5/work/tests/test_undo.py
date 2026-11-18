import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tasks.py"))


def run(cwd, *args):
    return subprocess.run([sys.executable, TASKS, *args], cwd=cwd,
                          capture_output=True, text=True)


class TestUndo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def lines(self, *args):
        return run(self.dir, *args).stdout.splitlines()

    def test_nothing_to_undo(self):
        r = run(self.dir, "undo")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stderr.strip(), "Nothing to undo")

    def test_undo_add_reuses_id(self):
        run(self.dir, "add", "A")
        self.assertEqual(run(self.dir, "undo").stdout.strip(), "Undone")
        self.assertEqual(self.lines("list"), ["No tasks"])
        self.assertEqual(run(self.dir, "add", "B").stdout.strip(), "Added 1")

    def test_undo_done_edit_delete_in_turn(self):
        run(self.dir, "add", "A")          # id 1
        run(self.dir, "done", "1")
        run(self.dir, "edit", "1", "--title", "Z")
        run(self.dir, "delete", "1")
        self.assertEqual(self.lines("list"), ["No tasks"])
        run(self.dir, "undo")  # undo delete
        self.assertEqual(self.lines("list"), ["1 [x] Z"])
        run(self.dir, "undo")  # undo edit
        self.assertEqual(self.lines("list"), ["1 [x] A"])
        run(self.dir, "undo")  # undo done
        self.assertEqual(self.lines("list"), ["1 [ ] A"])
        run(self.dir, "undo")
        self.assertEqual(self.lines("list"), ["No tasks"])
        self.assertEqual(run(self.dir, "undo").returncode, 1)

    def test_failed_commands_not_recorded(self):
        run(self.dir, "add", "A")
        run(self.dir, "done", "99")
        run(self.dir, "add", "B", "--priority", "bogus")
        run(self.dir, "undo")
        self.assertEqual(self.lines("list"), ["No tasks"])
        self.assertEqual(run(self.dir, "undo").returncode, 1)

    def test_undo_across_runs_and_next_id_restored(self):
        run(self.dir, "add", "A")
        run(self.dir, "add", "B")
        run(self.dir, "undo")  # separate process; removes B, next_id back to 2
        self.assertEqual(self.lines("list"), ["1 [ ] A"])
        self.assertEqual(run(self.dir, "add", "C").stdout.strip(), "Added 2")


if __name__ == "__main__":
    unittest.main()
