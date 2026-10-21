"""Checks a task before it is used (README, "Tasks"). Writes tasks/<ID>/validation.json.

- Start: at least one target test fails, and every `keeps...` (neighbour) test passes.
- Reference: tasks/<ID>/reference.patch makes every hidden test pass; with --full, the whole reactor passes too.
- Naive (neighbour-break tasks, tasks/<ID>/naive.patch): at least one `keeps...` test fails, and with --full the
  existing suite (hidden tests excluded) still passes, so the trap is real and the existing tests do not show it.
- Plant (tasks/<ID>/plant.patch, if any): with --full, the existing suite stays green with the plant.

Usage: python3 -I validate.py <ID> [<ID> ...] [--full]. Needs JDK 21, offline ~/.m2 and the shopizer clone ($SHOPIZER).
"""
import glob, json, os, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOP = os.environ.get("SHOPIZER", os.path.expanduser("~/code/benchmark/skills-impact-work/shopizer"))
HID = "sm-shop/src/test/java/com/salesmanager/test/shop/hidden"
MVN = "mvn -o -B -Dmaven.repo.local=$HOME/.m2/repository -Dmaven.test.failure.ignore=true"
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
    sh("rm -rf */target", work)
    p = sh(f"{MVN} -Dsurefire.failIfNoSpecifiedTests=false -pl sm-shop -am -Dtest='Hidden*' test", work)
    open(log, "w").write(p.stdout[-20000:])
    compiled = p.returncode == 0 and "COMPILATION ERROR" not in p.stdout
    return compiled, hidden_cases(work)


def existing_suite_green(work, log):
    p = sh(f"{MVN} -Dtest='!Hidden*' -Dsurefire.failIfNoSpecifiedTests=false clean test", work)
    open(log, "w").write(p.stdout[-30000:])
    return p.returncode == 0 and "Tests run:" in p.stdout and not any(
        "<<< FAILURE" in l or "<<< ERROR" in l for l in p.stdout.splitlines())


def fresh(tid, tmp, name):
    w = os.path.join(tmp, name)
    sh(f"git clone -q '{SHOP}' '{w}' && git -C '{w}' checkout -q 6a4a0a6", tmp)
    sh(f"TRIAL_QUESTION={tid} bash '{E}/scripts/setup.sh'", w)
    os.makedirs(os.path.join(w, HID), exist_ok=True)
    for f in glob.glob(os.path.join(E, "hidden", tid, "*.java")):
        shutil.copy(f, os.path.join(w, HID))
    return w


def validate(tid, full):
    t = os.path.join(E, "tasks", tid)
    tmp = tempfile.mkdtemp()
    res = {"task": tid}
    w = fresh(tid, tmp, "c")
    if full and os.path.exists(os.path.join(t, "plant.patch")):
        res["plant_suite_green"] = existing_suite_green(w, os.path.join(t, "validate-plant-full.log"))
    res["start_compiled"], res["start"] = run_hidden(w, os.path.join(t, "validate-start.log"))
    target = {n: o for n, o in res["start"].items() if not n.startswith("keeps")}
    keeps = {n: o for n, o in res["start"].items() if n.startswith("keeps")}
    start_ok = res["start_compiled"] and any(o != "pass" for o in target.values()) and all(o == "pass" for o in keeps.values())
    if os.path.exists(os.path.join(t, "naive.patch")):
        wn = fresh(tid, tmp, "n")
        if sh(f"git apply '{t}/naive.patch'", wn).returncode:
            res["naive_applies"] = False
        else:
            res["naive_applies"] = True
            res["naive_compiled"], res["naive"] = run_hidden(wn, os.path.join(t, "validate-naive.log"))
            res["naive_breaks_keeps"] = any(o != "pass" for n, o in res["naive"].items() if n.startswith("keeps"))
            if full:
                res["naive_suite_green"] = existing_suite_green(wn, os.path.join(t, "validate-naive-full.log"))
    naive_ok = "naive_applies" not in res or (res["naive_applies"] and res.get("naive_breaks_keeps")
                                             and (not full or res.get("naive_suite_green")))
    r = sh(f"git apply '{t}/reference.patch'", w)
    if r.returncode:
        res["reference_applies"] = False
        res["error"] = r.stderr
    else:
        res["reference_applies"] = True
        res["ref_compiled"], res["reference"] = run_hidden(w, os.path.join(t, "validate-ref.log"))
        if full:
            p = sh(f"{MVN} clean test", w)
            open(os.path.join(t, "validate-full.log"), "w").write(p.stdout[-30000:])
            out = os.path.join(tmp, "s")
            os.makedirs(out)
            n = sum(open(f).read().count("@Test") for f in glob.glob(os.path.join(E, "hidden", tid, "*.java")))
            sh(f"python3 -I '{E}/scripts/summarize.py' '{out}' {p.returncode} {n}", w)
            res["full"] = json.load(open(os.path.join(out, "verify-summary.json")))
    ref_ok = res.get("ref_compiled") and res.get("reference") and all(o == "pass" for o in res["reference"].values())
    res["valid"] = bool(start_ok and ref_ok and naive_ok and (not full or res["full"]["pass"])
                        and res.get("plant_suite_green", True))
    json.dump(res, open(os.path.join(t, "validation.json"), "w"), indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    return res


if __name__ == "__main__":
    full = "--full" in sys.argv
    for tid in [a for a in sys.argv[1:] if not a.startswith("--")]:
        r = validate(tid, full)
        print(tid, "VALID" if r["valid"] else "INVALID", "start:", r.get("start"), "ref:", r.get("reference"),
              "naive:", r.get("naive", "-"), "naive suite:", r.get("naive_suite_green", "-"),
              "full:", r.get("full", {}).get("pass") if full else "-", flush=True)
