import unittest
import tempfile

from test_add import run


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_case_insensitive_substring(self):
        run(self.dir, "add", "Buy Milk")
        run(self.dir, "add", "milkshake")
        run(self.dir, "add", "Walk dog")
        r = run(self.dir, "search", "milk")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] Buy Milk", "2 [ ] milkshake"])

    def test_no_matches(self):
        run(self.dir, "add", "Walk dog")
        r = run(self.dir, "search", "zzz")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "No matches")


if __name__ == "__main__":
    unittest.main()
