"""Imports the shared shop, policy, cases, grader and model client from 2026-10-need-an-agent unchanged, so the
architectures here run on exactly the same shop. Only the cases are extended (cases.py adds level 6).
"""
import os, sys

NA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                  "2026-10-need-an-agent", "src")
sys.path.append(NA)   # after this folder, so run.py, validate.py etc. here win
POLICY = open(os.path.join(NA, "policy.md")).read()
