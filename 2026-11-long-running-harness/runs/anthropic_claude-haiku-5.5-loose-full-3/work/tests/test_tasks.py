import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(os.path.dirname(HERE), "tasks.py")


class TasksTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def run_cmd(self, *args):
        p = subprocess.run([sys.executable, TASKS] + list(args), cwd=self.dir,
                           capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    def ok(self, *args):
        rc, out, err = self.run_cmd(*args)
        self.assertEqual(rc, 0, err)
        return out

    def fail(self, *args):
        rc, out, err = self.run_cmd(*args)
        self.assertEqual(rc, 1, (out, err))
        return err

    def test_f01_add(self):
        self.assertEqual(self.ok("add", "Buy milk"), "Added 1\n")
        self.assertEqual(self.ok("add", "Walk dog"), "Added 2\n")
        self.assertTrue(os.path.exists(os.path.join(self.dir, "tasks.json")))

    def test_f02_list(self):
        self.assertEqual(self.ok("list"), "No tasks\n")
        self.ok("add", "Buy milk")
        self.ok("add", "Walk dog")
        self.assertEqual(self.ok("list"), "1 [ ] Buy milk\n2 [ ] Walk dog\n")

    def test_f03_done(self):
        self.ok("add", "a")
        self.ok("add", "b")
        self.assertEqual(self.ok("done", "2"), "Done 2\n")
        self.assertIn("2 [x] b", self.ok("list"))
        self.assertIn("No such task: 9", self.fail("done", "9"))

    def test_f04_delete(self):
        self.ok("add", "a")
        self.ok("add", "b")
        self.assertEqual(self.ok("delete", "2"), "Deleted 2\n")
        self.assertEqual(self.ok("add", "c"), "Added 3\n")
        self.assertIn("No such task: 2", self.fail("delete", "2"))

    def test_f05_priority(self):
        self.ok("add", "a", "--priority", "high")
        self.ok("add", "b")
        self.ok("add", "c", "--priority", "low")
        self.ok("add", "d", "--priority", "high")
        self.assertIn("1 [ ] a (high)", self.ok("list"))
        self.assertEqual(self.ok("list", "--sort", "priority"),
                         "1 [ ] a (high)\n4 [ ] d (high)\n2 [ ] b\n3 [ ] c (low)\n")
        self.assertIn("Invalid priority: urgent",
                      self.fail("add", "x", "--priority", "urgent"))

    def test_f06_tags(self):
        self.ok("add", "a", "--tag", "work", "--tag", "home")
        self.ok("add", "b", "--tag", "home")
        self.assertIn("1 [ ] a #work #home", self.ok("list"))
        self.assertEqual(self.ok("list", "--tag", "work"), "1 [ ] a #work #home\n")

    def test_f07_due(self):
        self.ok("add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        self.assertIn("1 [ ] a (low) #t due:2026-03-01", self.ok("list"))
        self.assertIn("Invalid date: 2026-13-40",
                      self.fail("add", "x", "--due", "2026-13-40"))
        self.ok("add", "late", "--due", "2020-01-01")
        self.ok("add", "later", "--due", "2030-01-01")
        self.ok("add", "done-late", "--due", "2020-01-01")
        self.ok("done", "4")
        out = self.ok("list", "--overdue", "--today", "2026-06-01")
        self.assertEqual(out, "2 [ ] late due:2020-01-01\n")

    def test_f08_edit(self):
        self.ok("add", "a")
        self.assertEqual(self.ok("edit", "1", "--title", "New", "title"), "Edited 1\n")
        self.assertIn("1 [ ] New title", self.ok("list"))
        self.assertIn("No such task: 7", self.fail("edit", "7", "--title", "x"))

    def test_f09_search(self):
        self.ok("add", "Buy Milk")
        self.ok("add", "milkshake")
        self.ok("add", "walk dog")
        self.assertEqual(self.ok("search", "milk"),
                         "1 [ ] Buy Milk\n2 [ ] milkshake\n")
        self.assertEqual(self.ok("search", "zzz"), "No matches\n")

    def test_f10_export(self):
        import json
        self.assertEqual(json.loads(self.ok("export", "--format", "json")), [])
        self.ok("add", "a", "--tag", "x", "--tag", "y", "--due", "2026-01-02")
        self.ok("add", "b")
        self.ok("done", "2")
        recs = json.loads(self.ok("export", "--format", "json"))
        self.assertEqual(recs[0], {"id": 1, "title": "a", "done": False,
                                   "priority": "medium", "tags": ["x", "y"],
                                   "due": "2026-01-02"})
        self.assertEqual(recs[1]["done"], True)
        self.assertIsNone(recs[1]["due"])
        self.assertEqual(self.ok("export", "--format", "csv"),
                         "id,title,done,priority,tags,due\n"
                         "1,a,false,medium,x;y,2026-01-02\n"
                         "2,b,true,medium,,\n")

    def test_f11_stats(self):
        self.assertEqual(self.ok("stats"), "open: 0\ndone: 0\ntotal: 0\n")
        self.ok("add", "a")
        self.ok("add", "b")
        self.ok("add", "c")
        self.ok("done", "1")
        self.ok("delete", "2")
        self.assertEqual(self.ok("stats"), "open: 1\ndone: 1\ntotal: 2\n")

    def test_f12_undo(self):
        self.assertIn("Nothing to undo", self.fail("undo"))
        self.ok("add", "a")
        self.assertEqual(self.ok("undo"), "Undone\n")
        self.assertEqual(self.ok("add", "b"), "Added 1\n")
        self.ok("done", "1")
        self.ok("edit", "1", "--title", "z")
        self.ok("delete", "1")
        self.assertEqual(self.ok("list"), "No tasks\n")
        self.ok("undo")
        self.assertEqual(self.ok("list"), "1 [ ] z\n")
        self.ok("undo")
        self.assertEqual(self.ok("list"), "1 [x] b\n")
        self.ok("undo")
        self.assertEqual(self.ok("list"), "1 [ ] b\n")
        self.ok("undo")
        self.assertEqual(self.ok("list"), "No tasks\n")
        self.assertIn("Nothing to undo", self.fail("undo"))

    def test_failed_commands_not_recorded(self):
        self.ok("add", "a")
        self.fail("done", "9")
        self.fail("add", "x", "--priority", "bad")
        self.ok("undo")
        self.assertEqual(self.ok("list"), "No tasks\n")


if __name__ == "__main__":
    unittest.main()
