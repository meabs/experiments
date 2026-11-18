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


class TestUndo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_nothing_to_undo(self):
        r = run(self.dir, "undo")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Nothing to undo", r.stderr)

    def test_undo_add_reuses_id(self):
        run(self.dir, "add", "a")
        r = run(self.dir, "undo")
        self.assertEqual((r.returncode, r.stdout), (0, "Undone\n"))
        self.assertEqual(run(self.dir, "list").stdout, "No tasks\n")
        self.assertEqual(run(self.dir, "add", "b").stdout, "Added 1\n")

    def test_undo_done_edit_delete_in_turn(self):
        run(self.dir, "add", "a")          # 1
        run(self.dir, "done", "1")
        run(self.dir, "edit", "1", "--title", "new", "name")
        run(self.dir, "delete", "1")
        self.assertEqual(run(self.dir, "list").stdout, "No tasks\n")
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "list").stdout, "1 [x] new name\n")
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "list").stdout, "1 [x] a\n")
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "list").stdout, "1 [ ] a\n")
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "list").stdout, "No tasks\n")
        self.assertEqual(run(self.dir, "undo").returncode, 1)

    def test_failed_commands_not_recorded(self):
        run(self.dir, "add", "a")
        run(self.dir, "done", "9")
        run(self.dir, "add", "b", "--priority", "bogus")
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "list").stdout, "No tasks\n")

    def test_undo_across_runs_restores_next_id(self):
        run(self.dir, "add", "a")
        run(self.dir, "add", "b")
        run(self.dir, "delete", "2")
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "list").stdout, "1 [ ] a\n2 [ ] b\n")
        run(self.dir, "undo")
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "add", "c").stdout, "Added 1\n")


if __name__ == "__main__":
    unittest.main()
