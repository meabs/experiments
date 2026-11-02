"""Proof tests run against the target app (../target), never shown to the agents."""
import importlib.util
import os
import sys

TARGET = os.environ.get("VH_TARGET") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                     "target")
sys.path.insert(0, TARGET)
_spec = importlib.util.spec_from_file_location("target_conftest", os.path.join(TARGET, "tests", "conftest.py"))
_t = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_t)
app, client, priya, staff, login = _t.app, _t.client, _t.priya, _t.staff, _t.login
