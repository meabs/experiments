import unittest
import tempfile

from test_add import run


class TestEdit(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_edit_title(self):
        run(self.dir, "add", "Old")
        r = run(self.dir, "edit", "1", "--title", "New title")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Edited 1")
        r = run(self.dir, "list")
        self.assertEqual(r.stdout.splitlines(), ["1 [ ] New title"])

    def test_unknown_id(self):
        r = run(self.dir, "edit", "7", "--title", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 7", r.stderr)


if __name__ == "__main__":
    unittest.main()
