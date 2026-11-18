import unittest
import tempfile

from test_add import run


class TestTags(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_suffix_order(self):
        run(self.dir, "add", "a", "--tag", "work", "--tag", "home")
        run(self.dir, "add", "b", "--priority", "high", "--tag", "work")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(),
                         ["1 [ ] a #work #home", "2 [ ] b (high) #work"])

    def test_filter(self):
        run(self.dir, "add", "a", "--tag", "work")
        run(self.dir, "add", "b", "--tag", "home")
        run(self.dir, "add", "c", "--tag", "work")
        r = run(self.dir, "list", "--tag", "work")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] a #work", "3 [ ] c #work"])


if __name__ == "__main__":
    unittest.main()
