import unittest
import tempfile

from test_add import run


class TestStats(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_fresh(self):
        r = run(self.dir, "stats")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines(), ["open: 0", "done: 0", "total: 0"])

    def test_excludes_deleted(self):
        run(self.dir, "add", "a")
        run(self.dir, "add", "b")
        run(self.dir, "add", "c")
        run(self.dir, "done", "1")
        run(self.dir, "delete", "2")
        r = run(self.dir, "stats")
        self.assertEqual(r.stdout.splitlines(), ["open: 1", "done: 1", "total: 2"])


if __name__ == "__main__":
    unittest.main()
