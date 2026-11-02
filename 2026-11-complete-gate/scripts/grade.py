"""Grades one workspace for one ticket, independent of the fault and of anything the agent did to the tests.

Copies the workspace to a temporary folder, removes the fault files (EXCL and EXCL1 live in pom.xml, which is restored), restores
the test support, the existing tests and pom.xml to sec-authz's originals, adds the ticket's hidden tests (GRL's), and
runs the suite offline with the real Maven. Adapted from 2026-11-broken-tools/scripts/grade.py.

Usage: python3 -I grade.py <task> <workspace> [--overlay DIR ...]
  task: C1, C2, L1X (hidden tests L1), S2X (hidden tests S2)

Prints one JSON summary:
  build    compiled, the hidden tests ran and all 25 existing tests ran
  correct  build, every existing test and every hidden test passed (the tickets state every rule, so the r<letter>_
           tests count as part of the ticket here)
"""
import glob, json, os, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(os.path.dirname(E), "2026-10-sec-authz", "app")
TEST_ROOT = "src/test/java/com/example/accounts"
PROTECTED = [f"{TEST_ROOT}/support", f"{TEST_ROOT}/AccountApiTest.java", f"{TEST_ROOT}/CaseApiTest.java",
             f"{TEST_ROOT}/ClosureApiTest.java", f"{TEST_ROOT}/AdminCustomerApiTest.java", "src/test/resources/keys",
             "pom.xml"]
EXISTING = {"AccountApiTest", "CaseApiTest", "ClosureApiTest", "AdminCustomerApiTest"}
HIDDEN = {"C1": "C1", "C2": "C2", "L1X": "L1", "S2X": "S2"}
FAULT_FILES = [os.path.relpath(p, os.path.join(E, "faults", f)) for f in ()
               for p in glob.glob(os.path.join(E, "faults", f, "src", "**", "*.java"), recursive=True)]


def grade(task, workspace, overlays=()):
    tmp = tempfile.mkdtemp(prefix="cg-grade-")
    try:
        ws = os.path.join(tmp, "ws")
        shutil.copytree(workspace, ws, ignore=shutil.ignore_patterns(".git", "target"))
        for o in overlays:
            shutil.copytree(o, ws, dirs_exist_ok=True)
        for rel in FAULT_FILES:
            p = os.path.join(ws, rel)
            if os.path.exists(p):
                os.remove(p)
        for p in PROTECTED:
            src, dst = os.path.join(APP, p), os.path.join(ws, p)
            if os.path.isdir(src):
                shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)
            else:
                shutil.copy(src, dst)
        hidden_dir = os.path.join(ws, TEST_ROOT, "hidden")
        shutil.rmtree(hidden_dir, ignore_errors=True)
        os.makedirs(hidden_dir)
        h = HIDDEN[task]
        shutil.copy(os.path.join(E, "hidden", f"{h}HiddenTest.java"), hidden_dir)
        p = subprocess.run(["/usr/bin/mvn", "-B", "-o", "-q", "test", "-Dsurefire.failIfNoSpecifiedTests=false"],
                           cwd=ws, capture_output=True, text=True, timeout=900)
        cases = []
        for f in glob.glob(os.path.join(ws, "target", "surefire-reports", "TEST-*.xml")):
            for tc in ET.parse(f).getroot().iter("testcase"):
                bad = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
                cases.append({"class": tc.get("classname").rsplit(".", 1)[-1], "name": tc.get("name"),
                              "passed": bad is None and tc.find("skipped") is None,
                              "message": (bad.get("message") or "")[:300] if bad is not None else ""})
        hidden = [c for c in cases if c["class"] == f"{h}HiddenTest"]
        regression = [c for c in cases if c["class"] in EXISTING]
        build = bool(hidden) and len(regression) == 25
        correct = build and all(c["passed"] for c in hidden + regression)
        out = {"task": task, "build": build, "maven_exit": p.returncode,
               "regression": {"passed": sum(c["passed"] for c in regression), "total": len(regression)},
               "hidden": {"passed": sum(c["passed"] for c in hidden), "total": len(hidden)},
               "correct": correct,
               "failed": [f"{c['class']}.{c['name']}: {c['message']}" for c in cases if not c["passed"]]}
        if not build:
            out["build_log"] = (p.stdout + p.stderr)[-2000:]
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    overlays = []
    if "--overlay" in args:
        i = args.index("--overlay")
        overlays = args[i + 1:]
        args = args[:i]
    print(json.dumps(grade(args[0], args[1], overlays), indent=1))
