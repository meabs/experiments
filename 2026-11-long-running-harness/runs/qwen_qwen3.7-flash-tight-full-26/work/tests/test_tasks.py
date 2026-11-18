#!/usr/bin/env python3
"""Tests for tasks.py command-line task manager."""

import json
import os
import subprocess
import sys
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    """Feature F01: add"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_py = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, self.tasks_py] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_prints_added_id(self):
        result = self._run('add', 'Buy milk')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'Added 1')

    def test_add_second_task(self):
        self._run('add', 'Buy milk')
        result = self._run('add', 'Walk dog')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'Added 2')

    def test_tasks_json_created(self):
        self._run('add', 'Buy milk')
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'tasks.json')))

    def test_add_with_priority(self):
        result = self._run('add', 'Task', '--priority', 'high')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'Added 1')

    def test_add_with_tags(self):
        result = self._run('add', 'Task', '--tag', 'work')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'Added 1')

    def test_add_with_due(self):
        result = self._run('add', 'Task', '--due', '2025-12-25')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'Added 1')


class TestList(unittest.TestCase):
    """Feature F02: list"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_py = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, self.tasks_py] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_empty_list(self):
        result = self._run('list')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'No tasks')

    def test_list_shows_tasks(self):
        self._run('add', 'Buy milk')
        self._run('add', 'Walk dog')
        result = self._run('list')
        lines = result.stdout.strip().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [ ] Walk dog')


class TestDone(unittest.TestCase):
    """Feature F03: done"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_py = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, self.tasks_py] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_done_marks_task(self):
        self._run('add', 'Buy milk')
        result = self._run('done', '1')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'Done 1')

    def test_done_shows_x(self):
        self._run('add', 'Buy milk')
        self._run('done', '1')
        result = self._run('list')
        lines = result.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [x] Buy milk')

    def test_done_unknown_id(self):
        result = self._run('done', '99')
        self.assertEqual(result.returncode, 1)
        self.assertIn('No such task: 99', result.stderr)


class TestDelete(unittest.TestCase):
    """Feature F04: delete"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_py = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, self.tasks_py] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_delete_prints_deleted(self):
        self._run('add', 'Buy milk')
        result = self._run('delete', '1')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'Deleted 1')

    def test_ids_not_reused(self):
        self._run('add', 'Buy milk')
        self._run('delete', '1')
        result = self._run('add', 'New task')
        self.assertEqual(result.stdout.strip(), 'Added 2')

    def test_delete_unknown_id(self):
        result = self._run('delete', '99')
        self.assertEqual(result.returncode, 1)
        self.assertIn('No such task: 99', result.stderr)


if __name__ == '__main__':
    unittest.main()
