import unittest
import tempfile

from test_add import run


class TestUndo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_nothing_to_undo(self):
        r = run(self.dir, "undo")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Nothing to undo", r.stderr)

    def test_undo_add_reuses_id(self):
        run(self.dir, "add", "a")
        self.assertEqual(run(self.dir, "undo").stdout.strip(), "Undone")
        self.assertEqual(run(self.dir, "list").stdout.strip(), "No tasks")
        self.assertEqual(run(self.dir, "add", "b").stdout.strip(), "Added 1")

    def test_undo_chain(self):
        run(self.dir, "add", "a")          # 1
        run(self.dir, "add", "b")          # 2
        run(self.dir, "done", "1")
        run(self.dir, "edit", "2", "--title", "B2")
        run(self.dir, "delete", "1")
        run(self.dir, "undo")              # restore 1
        self.assertEqual(run(self.dir, "list").stdout.splitlines(),
                         ["1 [x] a", "2 [ ] B2"])
        run(self.dir, "undo")              # undo edit
        self.assertEqual(run(self.dir, "list").stdout.splitlines(),
                         ["1 [x] a", "2 [ ] b"])
        run(self.dir, "undo")              # undo done
        self.assertEqual(run(self.dir, "list").stdout.splitlines(),
                         ["1 [ ] a", "2 [ ] b"])
        run(self.dir, "undo")              # undo add b
        self.assertEqual(run(self.dir, "list").stdout.splitlines(), ["1 [ ] a"])
        self.assertEqual(run(self.dir, "add", "c").stdout.strip(), "Added 2")
        run(self.dir, "undo")
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "undo").returncode, 1)

    def test_failed_commands_not_recorded(self):
        run(self.dir, "add", "a")
        run(self.dir, "done", "99")        # fails
        run(self.dir, "add", "--priority", "bogus", "x")  # fails
        run(self.dir, "undo")
        self.assertEqual(run(self.dir, "list").stdout.strip(), "No tasks")
        self.assertEqual(run(self.dir, "undo").returncode, 1)

    def test_undo_across_runs(self):
        run(self.dir, "add", "a")
        run(self.dir, "add", "b")
        r = run(self.dir, "undo")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(run(self.dir, "list").stdout.splitlines(), ["1 [ ] a"])


if __name__ == "__main__":
    unittest.main()
