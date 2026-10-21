"""Checks a task before it is used: the hidden test must fail on the starting code (plant applied, if any) and pass
with tasks/<ID>/reference.patch. With --full, the whole reactor's tests must also pass with the reference.

Usage: python3 -I validate.py <ID> [<ID> ...] [--full]. Writes tasks/<ID>/validation.json. Needs JDK 21, offline ~/.m2
and the shopizer clone ($SHOPIZER).
"""
import glob, json, os, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOP = os.environ.get("SHOPIZER", os.path.expanduser("~/code/benchmark/skills-impact-work/shopizer"))
HID = "sm-shop/src/test/java/com/salesmanager/test/shop/hidden"
ENV = dict(os.environ, JAVA_HOME="/opt/homebrew/opt/openjdk@21",
           PATH="/opt/homebrew/opt/openjdk@21/bin:" + os.environ["PATH"])


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, env=ENV)


def hidden_cases(work):
    cases = {}
    for f in glob.glob(os.path.join(work, "sm-shop/target/surefire-reports/TEST-*.hidden.*.xml")):
        for tc in ET.parse(f).getroot().iter("testcase"):
            o = "fail" if tc.find("failure") is not None else "error" if tc.find("error") is not None else \
                "skipped" if tc.find("skipped") is not None else "pass"
            cases[tc.get("name")] = o
    return cases


def run_hidden(work, log):
    p = sh("mvn -o -B -Dmaven.repo.local=$HOME/.m2/repository -Dmaven.test.failure.ignore=true "
           "-Dsurefire.failIfNoSpecifiedTests=false -pl sm-shop -am -Dtest='Hidden*' test", work)
    open(log, "w").write(p.stdout[-20000:])
    compiled = p.returncode == 0 and "COMPILATION ERROR" not in p.stdout
    return compiled, hidden_cases(work)


def validate(tid, full):
    t = os.path.join(E, "tasks", tid)
    tmp = tempfile.mkdtemp()
    w = os.path.join(tmp, "c")
    sh(f"git clone -q '{SHOP}' '{w}' && git -C '{w}' checkout -q 6a4a0a6", tmp)
    sh(f"TRIAL_QUESTION={tid} bash '{E}/scripts/setup.sh'", w)
    os.makedirs(os.path.join(w, HID), exist_ok=True)
    for f in glob.glob(os.path.join(E, "hidden", tid, "*.java")):
        shutil.copy(f, os.path.join(w, HID))
    res = {"task": tid}
    if full and os.path.exists(os.path.join(t, "plant.patch")):
        # the existing suite must stay green with the plant, or the plant is visible to the agent
        p = sh("mvn -o -B -Dmaven.repo.local=$HOME/.m2/repository -Dmaven.test.failure.ignore=true -Dtest='!Hidden*' "
               "-Dsurefire.failIfNoSpecifiedTests=false clean test", w)
        open(os.path.join(t, "validate-plant-full.log"), "w").write(p.stdout[-30000:])
        res["plant_suite_green"] = p.returncode == 0 and "Tests run:" in p.stdout and not any(
            l for l in p.stdout.splitlines() if "<<< FAILURE" in l or "<<< ERROR" in l)
    res["start_compiled"], res["start"] = run_hidden(w, os.path.join(t, "validate-start.log"))
    r = sh(f"git apply '{t}/reference.patch'", w)
    if r.returncode:
        res["reference_applies"] = False
        res["error"] = r.stderr
    else:
        res["reference_applies"] = True
        sh("rm -rf */target", w)
        res["ref_compiled"], res["reference"] = run_hidden(w, os.path.join(t, "validate-ref.log"))
        if full:
            p = sh("mvn -o -B -Dmaven.repo.local=$HOME/.m2/repository -Dmaven.test.failure.ignore=true clean test", w)
            open(os.path.join(t, "validate-full.log"), "w").write(p.stdout[-30000:])
            out = os.path.join(tmp, "s")
            os.makedirs(out)
            n = sum(open(f).read().count("@Test") for f in glob.glob(os.path.join(E, "hidden", tid, "*.java")))
            q = sh(f"python3 -I '{E}/scripts/summarize.py' '{out}' {p.returncode} {n}", w)
            res["full"] = json.load(open(os.path.join(out, "verify-summary.json")))
    start_ok = not res["start_compiled"] or any(o != "pass" for o in res["start"].values())
    ref_ok = res.get("ref_compiled") and res["reference"] and all(o == "pass" for o in res["reference"].values())
    res["valid"] = bool(start_ok and ref_ok and (not full or res["full"]["pass"]) and res.get("plant_suite_green", True))
    json.dump(res, open(os.path.join(t, "validation.json"), "w"), indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    return res


if __name__ == "__main__":
    full = "--full" in sys.argv
    for tid in [a for a in sys.argv[1:] if not a.startswith("--")]:
        r = validate(tid, full)
        print(tid, "VALID" if r["valid"] else "INVALID", "start:", r.get("start"), "ref:", r.get("reference"),
              "full:", r.get("full", {}).get("pass") if full else "-", "plant suite:", r.get("plant_suite_green", "-"), flush=True)
