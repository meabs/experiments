import os
import unittest

from test_add import run
import tempfile


class TestList(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_empty(self):
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.strip(), "No tasks")

    def test_two_tasks(self):
        run(self.dir, "add", "Buy milk")
        run(self.dir, "add", "Walk dog")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] Buy milk", "2 [ ] Walk dog"])


if __name__ == "__main__":
    unittest.main()
