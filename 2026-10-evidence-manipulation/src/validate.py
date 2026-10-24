"""One command to validate the experiment: rebuilds the scenarios and variants, runs every test, prints dataset hashes.
Usage: python3 -I src/validate.py
"""
import hashlib, os, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
for s in ("scenarios.py", "variants.py"):
    subprocess.run([sys.executable, "-I", os.path.join(HERE, s)], check=True)
res = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests")))
for f in ("scenarios/scenarios.json", "scenarios/ground_truth.json", "manipulations/variants.json"):
    print(f, hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest())
sys.exit(0 if res.wasSuccessful() else 1)
