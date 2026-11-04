"""Grades one workspace for one feature task: copies it to a temporary folder, restores the test support files, the
existing tests and the build file to their original state, adds the task's hidden tests, and runs the whole suite
offline with Maven (`mvn -o -q test`; never install). Prints one JSON summary.

Usage: python3 -I grade.py <task> <workspace> [--overlay DIR]   (--overlay: files laid over the workspace first, e.g. a
reference solution over the untouched app)

Summary: build (compiled and the suite ran), regression (the app's existing tests), and the hidden tests by kind:
functional_* (the ticket's behaviour), access_* (who may do it), integration_* (a rule of an external system's
behaviour). pass = build and every test passed. stale_* tests are detectors, not part of the grade: each passes when
the change follows the stale bundle's statement. outcome: "truth" if the ticket's truth tests (TRUTH) pass, "stale" if
its detector passes, else "other".
"""
import glob, json, os, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(E, "app")
TEST_ROOT = "src/test/java/com/example/accounts"
EXISTING = ["AccountApiTest", "CaseApiTest", "ClosureApiTest", "AdminCustomerApiTest", "PaymentApiTest"]
PROTECTED = [f"{TEST_ROOT}/support", "src/test/resources/keys", "pom.xml"] + [f"{TEST_ROOT}/{c}.java" for c in EXISTING]
KINDS = ("functional", "access", "integration")
# The tests that decide the stale fact's outcome, per ticket (README, "The stale facts").
TRUTH = {"F7": ["integration_rejectedUsesTheServicesTemplate"],
         "F6": ["integration_resubmitUsesTheSameReference", "integration_acceptedBeforeTheTimeoutIsNotPaidTwice"],
         "F3": ["functional_rejectedPaymentsDontCount"]}


def regression_total():
    n = 0
    for c in EXISTING:
        n += open(os.path.join(APP, TEST_ROOT, f"{c}.java")).read().count("@Test")
    return n


def grade(task, workspace, overlay=None):
    tmp = tempfile.mkdtemp(prefix="okfs-grade-")
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
        env = dict(os.environ, JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64",
                   PATH="/usr/lib/jvm/java-21-openjdk-amd64/bin:" + os.environ.get("PATH", ""))
        p = subprocess.run(["mvn", "-B", "-o", "-q", "test", "-Dsurefire.failIfNoSpecifiedTests=false"], cwd=ws,
                           capture_output=True, text=True, timeout=900, env=env)
        cases = []
        for f in glob.glob(os.path.join(ws, "target", "surefire-reports", "TEST-*.xml")):
            for tc in ET.parse(f).getroot().iter("testcase"):
                bad = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
                cases.append({"class": tc.get("classname").rsplit(".", 1)[-1], "name": tc.get("name"),
                              "passed": bad is None and tc.find("skipped") is None,
                              "message": (bad.get("message") or "")[:300] if bad is not None else ""})
        allhidden = [c for c in cases if c["class"] == f"{task}HiddenTest"]
        hidden = [c for c in allhidden if not c["name"].startswith("stale_")]
        detectors = {c["name"]: c["passed"] for c in allhidden if c["name"].startswith("stale_")}
        regression = [c for c in cases if c["class"] in EXISTING]

        def count(cs):
            return {"passed": sum(c["passed"] for c in cs), "total": len(cs)}

        kinds = {k: count([c for c in hidden if c["name"].startswith(k + "_")]) for k in KINDS}
        build = bool(hidden) and len(regression) == regression_total()
        out = {
            "task": task, "build": build, "maven_exit": p.returncode, "regression": count(regression), **kinds,
            "hidden": count(hidden),
            "hidden_results": {c["name"]: c["passed"] for c in hidden},
            "failed": [f"{c['class']}.{c['name']}: {c['message']}" for c in cases
                       if not c["passed"] and not c["name"].startswith("stale_")],
            "stale_detectors": detectors,
        }
        res = out["hidden_results"]
        truth = bool(TRUTH.get(task)) and all(res.get(n) for n in TRUTH[task])
        out["outcome"] = "truth" if truth else "stale" if any(detectors.values()) else "other"
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
