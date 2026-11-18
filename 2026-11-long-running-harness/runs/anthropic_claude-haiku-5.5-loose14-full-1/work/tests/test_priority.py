import unittest
import tempfile

from test_add import run


class TestPriority(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_suffix(self):
        run(self.dir, "add", "a", "--priority", "high")
        run(self.dir, "add", "b", "--priority", "low")
        run(self.dir, "add", "c")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a (high)", "2 [ ] b (low)", "3 [ ] c"])

    def test_sort_priority(self):
        run(self.dir, "add", "low1", "--priority", "low")
        run(self.dir, "add", "med1")
        run(self.dir, "add", "high1", "--priority", "high")
        run(self.dir, "add", "med2", "--priority", "medium")
        run(self.dir, "add", "high2", "--priority", "high")
        r = run(self.dir, "list", "--sort", "priority")
        self.assertEqual(r.stdout.splitlines(), [
            "3 [ ] high1 (high)", "5 [ ] high2 (high)",
            "2 [ ] med1", "4 [ ] med2",
            "1 [ ] low1 (low)"])

    def test_invalid_priority(self):
        r = run(self.dir, "add", "x", "--priority", "urgent")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid priority: urgent", r.stderr)


if __name__ == "__main__":
    unittest.main()
