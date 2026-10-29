"""Grades one workspace for one task: copies it to a temporary folder, restores the test support files and the
existing tests to their original state, adds the task's hidden tests, and runs the whole suite offline with Maven
(`mvn -o -q test`; never install). Prints one JSON summary.

Usage: python3 -I grade.py <task> <workspace> [--overlay DIR]   (--overlay: files laid over the workspace first, e.g. a
reference solution over the untouched app)

Summary: build (compiled and the suite ran), regression (the app's existing tests), and the hidden tests by kind:
functional_*, allows_* (permitted access works), denies_* (refused access is refused). pass = build and every test passed.
Failing denies_ tests are split into denies_code_only (refused, but 403 where the convention is 404 or the reverse) and
denies_breach (everything else: allowed, leaked data, or changed state).
"""
import glob, json, os, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(E, "app")
TEST_ROOT = "src/test/java/com/example/accounts"
PROTECTED = [f"{TEST_ROOT}/support", f"{TEST_ROOT}/AccountApiTest.java", f"{TEST_ROOT}/CaseApiTest.java",
             f"{TEST_ROOT}/ClosureApiTest.java", f"{TEST_ROOT}/AdminCustomerApiTest.java", "src/test/resources/keys",
             "pom.xml"]


def grade(task, workspace, overlay=None):
    tmp = tempfile.mkdtemp(prefix="sec-grade-")
    try:
        ws = os.path.join(tmp, "ws")
        shutil.copytree(workspace, ws, ignore=shutil.ignore_patterns(".git", "target"))
        if overlay:
            shutil.copytree(overlay, ws, dirs_exist_ok=True)
        # The grader's own copies of the test support, the existing tests and the build file: an agent's edits to them
        # cannot make the evaluation easier.
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
        existing = {"AccountApiTest", "CaseApiTest", "ClosureApiTest", "AdminCustomerApiTest"}
        regression = [c for c in cases if c["class"] in existing]

        def count(cs):
            return {"passed": sum(c["passed"] for c in cs), "total": len(cs)}

        kinds = {k: count([c for c in hidden if c["name"].startswith(k + "_")]) for k in ("functional", "allows", "denies")}
        build = bool(hidden) and len(regression) == 25
        out = {
            "task": task, "build": build, "maven_exit": p.returncode, "regression": count(regression), **kinds,
            "hidden": count(hidden),
            "failed": [f"{c['class']}.{c['name']}: {c['message']}" for c in cases if not c["passed"]],
        }
        # Severity of each failing denies_ test: a "wrong denial code" failure refused the request with 403 where the API
        # convention is 404 (or the reverse); anything else (allowed, leaked data, changed state) is an access breach.
        swap = ("expected:<404> but was:<403>", "expected:<403> but was:<404>")
        out["denies_code_only"] = [c["name"] for c in hidden if c["name"].startswith("denies_") and not c["passed"]
                                   and any(x in c["message"] for x in swap)]
        out["denies_breach"] = [c["name"] for c in hidden if c["name"].startswith("denies_") and not c["passed"]
                                and c["name"] not in out["denies_code_only"]]
        out["pass"] = build and all(c["passed"] for c in hidden + regression) and out["hidden"]["total"] > 0
        if not build:
            out["build_log"] = (p.stdout + p.stderr)[-2000:]
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    overlay = None
    if "--overlay" in args:
        i = args.index("--overlay")
        overlay = args[i + 1]
        del args[i:i + 2]
    r = grade(args[0], args[1], overlay)
    print(json.dumps(r, indent=1))
    sys.exit(0 if r["pass"] else 1)
