import unittest
import tempfile

from test_add import run


class TestDue(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_suffix(self):
        run(self.dir, "add", "a", "--priority", "low", "--tag", "t", "--due", "2026-03-01")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a (low) #t due:2026-03-01"])

    def test_invalid_date(self):
        r = run(self.dir, "add", "a", "--due", "2026-13-40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Invalid date: 2026-13-40", r.stderr)

    def test_overdue(self):
        run(self.dir, "add", "old", "--due", "2026-01-01")
        run(self.dir, "add", "future", "--due", "2026-12-31")
        run(self.dir, "add", "nodue")
        run(self.dir, "add", "done-old", "--due", "2026-01-02")
        run(self.dir, "done", "4")
        r = run(self.dir, "list", "--overdue", "--today", "2026-06-01")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] old due:2026-01-01"])


if __name__ == "__main__":
    unittest.main()
