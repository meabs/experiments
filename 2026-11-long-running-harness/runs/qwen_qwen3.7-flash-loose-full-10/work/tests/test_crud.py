import subprocess
import json
import os
import sys
import tempfile
import unittest

TASKS_PY = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


def run(*args, cwd=None):
    """Run tasks.py with given args and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        [sys.executable, TASKS_PY] + list(args),
        capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestF01_Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_add_creates_task_and_prints_id(self):
        out, err, rc = run('add', 'Buy milk', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Added 1')
        # Check tasks.json exists
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'tasks.json')))

    def test_add_second_task_gets_id_2(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        out, err, rc = run('add', 'Walk dog', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Added 2')


class TestF02_List(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_empty_list(self):
        out, err, rc = run('list', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'No tasks')

    def test_list_shows_tasks_in_order(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        run('add', 'Walk dog', cwd=self.tmpdir)
        out, err, rc = run('list', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        lines = out.split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [ ] Walk dog')


class TestF03_Done(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_done_marks_task_done(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        out, err, rc = run('done', '1', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Done 1')
        # Verify via list
        out, _, _ = run('list', cwd=self.tmpdir)
        self.assertIn('[x]', out)

    def test_done_unknown_id_fails(self):
        out, err, rc = run('done', '99', cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertEqual(err, 'No such task: 99')


class TestF04_Delete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_delete_removes_task(self):
        run('add', 'Buy milk', cwd=self.tmpdir)
        run('add', 'Walk dog', cwd=self.tmpdir)
        out, err, rc = run('delete', '2', cwd=self.tmpdir)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'Deleted 2')
        # Next add should get id 3
        out, _, _ = run('add', 'New task', cwd=self.tmpdir)
        self.assertEqual(out, 'Added 3')

    def test_delete_unknown_id_fails(self):
        out, err, rc = run('delete', '99', cwd=self.tmpdir)
        self.assertEqual(rc, 1)
        self.assertEqual(err, 'No such task: 99')


if __name__ == '__main__':
    unittest.main()
