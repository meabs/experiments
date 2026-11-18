#!/usr/bin/env python3
"""Test feature: tags --tag repeatable, suffix '#work #home', list --tag work filters"""
import subprocess
import os
import tempfile
import shutil
import unittest


class TestF06Tags(unittest.TestCase):
    """Test feature: tags --tag repeatable, suffix '#work #home', list --tag work filters"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy(src, os.path.join(self.tmpdir, 'tasks.py'))
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        if os.path.exists(os.path.join(self.tmpdir, "tasks.json")):
            os.remove(os.path.join(self.tmpdir, "tasks.json"))

    def _run(self, *args):
        result = subprocess.run(
            ["python3", "tasks.py"] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_with_tag_shows_suffix(self):
        """add a --tag work --tag home; list shows '1 [ ] a #work #home'"""
        r = self._run("add", "a", "--tag", "work", "--tag", "home")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "Added 1")
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] a #work #home")

    def test_list_tag_filter(self):
        """list --tag work shows only matching tasks"""
        self._run("add", "a", "--tag", "work")
        self._run("add", "b", "--tag", "home")
        r = self._run("list", "--tag", "work")
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertIn("#work", lines[0])
        self.assertNotIn("b", lines[0])

    def test_suffix_order_priority_then_tags(self):
        """suffix order: priority then tags"""
        r = self._run("add", "a", "--priority", "high", "--tag", "work")
        self.assertEqual(r.returncode, 0)
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] a (high) #work")

    def test_multiple_tags_preserve_order(self):
        """tags appear in the order given"""
        r = self._run("add", "a", "--tag", "beta", "--tag", "alpha")
        self.assertEqual(r.returncode, 0)
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertEqual(lines[0], "1 [ ] a #beta #alpha")

    def test_no_tags_no_suffix(self):
        """task without tags has no tag suffix"""
        r = self._run("add", "a")
        self.assertEqual(r.returncode, 0)
        r2 = self._run("list")
        lines = r2.stdout.strip().split('\n')
        self.assertNotIn("#", lines[0])


if __name__ == "__main__":
    unittest.main()
