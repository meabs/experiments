"""Score a workdir against the hidden tests. Prints JSON: {"F01": true, ...}.

Usage: python3 score.py PATH_TO_TASKS_PY
A feature passes only if every test in its class passes. A missing tasks.py fails everything.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def score(tasks_py):
    os.environ['TASKS_PY'] = os.path.abspath(tasks_py)
    sys.path.insert(0, HERE)
    import test_features as tf
    classes = [(n, c) for n, c in vars(tf).items()
               if isinstance(c, type) and issubclass(c, unittest.TestCase) and n[0] == 'F' and n[1:3].isdigit()]
    out = {}
    for name, cls in sorted(classes):
        res = unittest.TestResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(cls).run(res)
        out[name[:3]] = res.wasSuccessful()
    return out


if __name__ == '__main__':
    print(json.dumps(score(sys.argv[1])))
