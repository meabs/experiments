import unittest
import tempfile

from test_add import run


class TestDone(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_done_marks_task(self):
        run(self.dir, "add", "Buy milk")
        run(self.dir, "add", "Walk dog")
        r = run(self.dir, "done", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Done 2")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] Buy milk", "2 [x] Walk dog"])

    def test_unknown_id(self):
        r = run(self.dir, "done", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
