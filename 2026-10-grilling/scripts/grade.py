"""Grades one workspace for one task: copies it to a temporary folder, restores the test support files, the existing
tests and the build file to sec-authz's originals, adds the task's hidden tests, and runs the suite offline
(`mvn -o -q test`).

Usage: python3 -I grade.py <task> <workspace> [--overlay DIR ...]
  task: C1, C2, S1, S2, L1, L2, or a follow-up S1F, S2F, L1F, L2F
  --overlay: folders laid over the workspace first, in order (e.g. reference/base reference/S1 for the reference)

Hidden test names start with ticket_ (what the ticket says) or r<letter>_ (one left-out requirement, from the task's
developer brief). A requirement is met when all its tests pass. Prints one JSON summary:
  build        compiled, the hidden tests ran and all 25 existing tests ran
  ticket_pass  build, every existing test and every ticket_ test passed
  reqs         {letter: passed?} for each left-out requirement
  met          left-out requirements met, counted only when ticket_pass (a broken change meets nothing)
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(os.path.dirname(E), "2026-10-sec-authz", "app")
TEST_ROOT = "src/test/java/com/example/accounts"
PROTECTED = [f"{TEST_ROOT}/support", f"{TEST_ROOT}/AccountApiTest.java", f"{TEST_ROOT}/CaseApiTest.java",
             f"{TEST_ROOT}/ClosureApiTest.java", f"{TEST_ROOT}/AdminCustomerApiTest.java", "src/test/resources/keys",
             "pom.xml"]
EXISTING = {"AccountApiTest", "CaseApiTest", "ClosureApiTest", "AdminCustomerApiTest"}


def grade(task, workspace, overlays=()):
    tmp = tempfile.mkdtemp(prefix="grill-grade-")
    try:
        ws = os.path.join(tmp, "ws")
        shutil.copytree(workspace, ws, ignore=shutil.ignore_patterns(".git", "target"))
        for o in overlays:
            shutil.copytree(o, ws, dirs_exist_ok=True)
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
        shutil.copy(os.path.join(E, "hidden", f"{task}HiddenTest.java"), hidden_dir)
        p = subprocess.run(["mvn", "-B", "-o", "-q", "test", "-Dsurefire.failIfNoSpecifiedTests=false"], cwd=ws,
                           capture_output=True, text=True, timeout=900)
        cases = []
        for f in glob.glob(os.path.join(ws, "target", "surefire-reports", "TEST-*.xml")):
            for tc in ET.parse(f).getroot().iter("testcase"):
                bad = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
                cases.append({"class": tc.get("classname").rsplit(".", 1)[-1], "name": tc.get("name"),
                              "passed": bad is None and tc.find("skipped") is None,
                              "message": (bad.get("message") or "")[:300] if bad is not None else ""})
        hidden = [c for c in cases if c["class"] == f"{task}HiddenTest"]
        regression = [c for c in cases if c["class"] in EXISTING]
        build = bool(hidden) and len(regression) == 25
        ticket = [c for c in hidden if c["name"].startswith("ticket_")]
        ticket_pass = build and all(c["passed"] for c in ticket + regression) and bool(ticket)
        letters = sorted({m.group(1) for c in hidden if (m := re.match(r"r([a-z])_", c["name"]))})
        reqs = {l: all(c["passed"] for c in hidden if c["name"].startswith(f"r{l}_")) for l in letters}
        out = {"task": task, "build": build, "maven_exit": p.returncode,
               "regression": {"passed": sum(c["passed"] for c in regression), "total": len(regression)},
               "ticket": {"passed": sum(c["passed"] for c in ticket), "total": len(ticket)},
               "ticket_pass": ticket_pass, "reqs": reqs, "met": sum(reqs.values()) if ticket_pass else 0,
               "possible": len(letters),
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
    r = grade(args[0], args[1], overlays)
    print(json.dumps(r, indent=1))
