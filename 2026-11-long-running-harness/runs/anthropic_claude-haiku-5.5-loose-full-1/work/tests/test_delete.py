import unittest
import tempfile

from test_add import run


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_delete_removes_and_ids_not_reused(self):
        run(self.dir, "add", "Buy milk")
        run(self.dir, "add", "Walk dog")
        r = run(self.dir, "delete", "2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Deleted 2")
        self.assertEqual(run(self.dir, "list").stdout.splitlines(), ["1 [ ] Buy milk"])
        self.assertEqual(run(self.dir, "add", "New").stdout.strip(), "Added 3")

    def test_unknown_id(self):
        r = run(self.dir, "delete", "9")
        self.assertEqual(r.returncode, 1)
        self.assertIn("No such task: 9", r.stderr)


if __name__ == "__main__":
    unittest.main()
