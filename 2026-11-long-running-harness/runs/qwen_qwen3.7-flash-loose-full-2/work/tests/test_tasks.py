"""Tests for tasks.py - command-line task manager."""

import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TasksTestBase(unittest.TestCase):
    """Base class that sets up a temp directory with tasks.py."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)
        # Copy tasks.py into the temp dir
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy2(src, os.path.join(self.tmpdir, 'tasks.py'))

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmpdir)

    def run_tasks(self, *args):
        """Run tasks.py with given arguments and return (stdout, stderr, returncode)."""
        result = subprocess.run(
            ['python3', 'tasks.py'] + list(args),
            capture_output=True, text=True
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def run_tasks_check(self, *args, expected_stdout=None, expected_stderr=None, expected_code=0):
        """Run tasks.py and check results."""
        stdout, stderr, code = self.run_tasks(*args)
        if expected_code is not None:
            self.assertEqual(code, expected_code, f"Expected exit code {expected_code}, got {code}. stderr: {stderr}")
        if expected_stdout is not None:
            self.assertEqual(stdout, expected_stdout, f"Expected stdout '{expected_stdout}', got '{stdout}'")
        if expected_stderr is not None:
            self.assertEqual(stderr, expected_stderr, f"Expected stderr '{expected_stderr}', got '{stderr}'")
        return stdout, stderr, code


class TestF01_Add(TasksTestBase):
    """Feature 1: add - add TITLE creates an open task and prints 'Added <id>'."""

    def test_add_single_task(self):
        stdout, _, _ = self.run_tasks_check('add', 'Buy milk', expected_stdout='Added 1')
        self.assertTrue(os.path.exists('tasks.json'))

    def test_add_second_task(self):
        self.run_tasks('add', 'Buy milk')
        stdout, _, _ = self.run_tasks_check('add', 'Walk dog', expected_stdout='Added 2')

    def test_tasks_json_exists(self):
        self.run_tasks('add', 'test')
        self.assertTrue(os.path.exists('tasks.json'))
        with open('tasks.json') as f:
            data = json.load(f)
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['next_id'], 2)


class TestF02_List(TasksTestBase):
    """Feature 2: list - prints one line per task in id order, or 'No tasks'."""

    def test_empty_list(self):
        self.run_tasks_check('list', expected_stdout='No tasks')

    def test_list_two_tasks(self):
        self.run_tasks('add', 'Buy milk')
        self.run_tasks('add', 'Walk dog')
        stdout, _, _ = self.run_tasks_check('list')
        lines = stdout.split('\n')
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [ ] Walk dog')


class TestF03_Done(TasksTestBase):
    """Feature 3: done - marks done, prints 'Done <id>'; unknown id -> error."""

    def test_done_task(self):
        self.run_tasks('add', 'Buy milk')
        self.run_tasks_check('done', '1', expected_stdout='Done 1')
        stdout, _, _ = self.run_tasks_check('list')
        self.assertIn('[x]', stdout)

    def test_done_unknown_id(self):
        _, stderr, code = self.run_tasks_check('done', '99', expected_stderr='No such task: 99', expected_code=1)


class TestF04_Delete(TasksTestBase):
    """Feature 4: delete - removes the task, prints 'Deleted <id>'; ids never reused."""

    def test_delete_task(self):
        self.run_tasks('add', 'Buy milk')
        self.run_tasks('add', 'Walk dog')
        self.run_tasks_check('delete', '2', expected_stdout='Deleted 2')
        stdout, _, _ = self.run_tasks_check('list')
        self.assertEqual(stdout, '1 [ ] Buy milk')

    def test_delete_next_id_not_reused(self):
        self.run_tasks('add', 'Buy milk')
        self.run_tasks('add', 'Walk dog')
        self.run_tasks('delete', '2')
        stdout, _, _ = self.run_tasks_check('add', 'New task', expected_stdout='Added 3')

    def test_delete_unknown_id(self):
        _, stderr, code = self.run_tasks_check('delete', '99', expected_stderr='No such task: 99', expected_code=1)


if __name__ == '__main__':
    unittest.main()
