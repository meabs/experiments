"""Retrospective "tests that bite" with per-defect mutation states (BUG task).

Each BUG run's own test changes (files under src/test only) are applied to four versions of the code and the
changed test classes are run:

  both    both planted defects (what the agent started from)
  price   only the ProductPriceUtils defect (tasks/BUG/v1/plant.patch)
  mapper  only the PersistableProductAvailabilityMapper defect (tasks/BUG/v2/plant.patch)
  fixed   both defects corrected (plant.patch + reference.patch)

A test case "detects" a state only if it passes on `fixed` and fails or errors on that state. A compile error,
or a test that also fails on `fixed`, never counts as detection. The hidden test is run through the same path as
a control: it must detect both defects independently.

Usage: python3 -I mutation.py <runs dir> <out json> [--logs <dir>] [--only KEY ...]
Needs JDK 21, the shopizer clone ($SHOPIZER) and the offline Maven repository used by verify.sh.
"""
import argparse, glob, gzip, json, os, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATES = ["both", "price", "mapper", "fixed"]
PATCHES = {"both": ["plant.patch"], "price": ["v1/plant.patch"], "mapper": ["v2/plant.patch"],
           "fixed": ["plant.patch", "reference.patch"]}
HIDDEN = "sm-shop/src/test/java/com/salesmanager/test/shop/hidden/HiddenSpecialPriceApiTest.java"


# ---------- pure classification (unit-tested in tests/test_grading.py) ----------

def classify(state_results):
    """state_results: {state: {"compiled": bool, "cases": {case: "pass"|"fail"|"error"|"skipped"}}}.

    Returns (verdict, detail). Verdicts: not-executable, fails-on-fixed, both, price-only, mapper-only,
    combined-only, none."""
    if any(not state_results.get(s, {}).get("compiled", False) for s in STATES):
        return "not-executable", {"reason": "does not compile or run in every state"}
    fixed = state_results["fixed"]["cases"]
    if not fixed:
        return "not-executable", {"reason": "no test case ran on fixed code"}
    valid = [c for c, o in fixed.items() if o == "pass"]
    red_on_fixed = sorted(c for c, o in fixed.items() if o in ("fail", "error"))
    if not valid:
        return "fails-on-fixed", {"red_on_fixed": red_on_fixed}

    def detecting(state):
        cases = state_results[state]["cases"]
        return sorted(c for c in valid if cases.get(c) in ("fail", "error"))

    det = {s: detecting(s) for s in ("both", "price", "mapper")}
    if det["price"] and det["mapper"]:
        v = "both"
    elif det["price"]:
        v = "price-only"
    elif det["mapper"]:
        v = "mapper-only"
    elif det["both"]:
        v = "combined-only"
    else:
        v = "none"
    return v, {"detecting": det, "valid_cases": len(valid), "red_on_fixed": red_on_fixed}


def read_reports(work, classes):
    """Outcome per test case from surefire XML, for the given simple class names only."""
    cases = {}
    for f in glob.glob(os.path.join(work, "**/target/surefire-reports/TEST-*.xml"), recursive=True):
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        for tc in root.iter("testcase"):
            cls = tc.get("classname", "")
            if cls.split(".")[-1] not in classes:
                continue
            o = "pass"
            if tc.find("failure") is not None:
                o = "fail"
            elif tc.find("error") is not None:
                o = "error"
            elif tc.find("skipped") is not None:
                o = "skipped"
            cases[f"{cls.split('.')[-1]}.{tc.get('name')}"] = o
    return cases


# ---------- execution ----------

def sh(cmd, cwd, log=None):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if log:
        with gzip.open(log, "wt") as fh:
            fh.write(p.stdout + p.stderr)
    return p


def build_bases(tmp, shopizer):
    for s in STATES:
        d = os.path.join(tmp, "base-" + s)
        sh(f"git clone -q '{shopizer}' '{d}' && git -C '{d}' checkout -q 6a4a0a6", tmp)
        sh(f"bash '{E}/scripts/setup.sh'", d)  # no TRIAL_QUESTION: resets history only
        for p in PATCHES[s]:
            r = sh(f"git apply '{E}/tasks/BUG/{p}'", d)
            if r.returncode:
                sys.exit(f"cannot build state {s}: {p}: {r.stderr}")


def run_one(key, test_files, apply_cmd, tmp, logs):
    mods = sorted({f.split("/")[0] for f in test_files})
    classes = sorted({os.path.basename(f)[:-5] for f in test_files if f.endswith(".java")})
    out = {}
    for s in STATES:
        w = os.path.join(tmp, key.replace("/", "_") + "-" + s)
        shutil.copytree(os.path.join(tmp, "base-" + s), w, symlinks=True)
        if apply_cmd(w).returncode:
            out[s] = {"compiled": False, "cases": {}, "note": "test diff does not apply"}
            shutil.rmtree(w, ignore_errors=True)
            continue
        log = os.path.join(logs, key.replace("/", "_") + f"-{s}.log.gz") if logs else None
        p = sh("mvn -o -B -Dmaven.repo.local=\"$HOME/.m2/repository\" -Dmaven.test.failure.ignore=true "
               f"-Dsurefire.failIfNoSpecifiedTests=false -pl {','.join(mods)} -am -Dtest={','.join(classes)} test",
               w, log)
        compiled = p.returncode == 0 and "COMPILATION ERROR" not in p.stdout
        out[s] = {"compiled": compiled, "cases": read_reports(w, set(classes)) if compiled else {}}
        shutil.rmtree(w, ignore_errors=True)
    verdict, detail = classify(out)
    return key, {"verdict": verdict, "detail": detail, "states": out, "classes": classes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs"); ap.add_argument("out")
    ap.add_argument("--logs"); ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@21"
    os.environ["PATH"] = "/opt/homebrew/opt/openjdk@21/bin:" + os.environ["PATH"]
    shopizer = os.environ.get("SHOPIZER", os.path.expanduser("~/code/benchmark/skills-impact-work/shopizer"))
    if a.logs:
        os.makedirs(a.logs, exist_ok=True)
    tmp = tempfile.mkdtemp()
    build_bases(tmp, shopizer)
    jobs = []
    # Control: the hidden test itself, copied in as if an agent had written it.
    hidden_src = os.path.join(E, "hidden/BUG/HiddenSpecialPriceApiTest.java")
    def copy_hidden(w):
        os.makedirs(os.path.dirname(os.path.join(w, HIDDEN)), exist_ok=True)
        shutil.copy(hidden_src, os.path.join(w, HIDDEN))
        return subprocess.CompletedProcess("", 0)
    jobs.append(("control/hidden", [HIDDEN], copy_hidden))
    for rd in sorted(glob.glob(os.path.join(a.runs, "BUG/*/*/*"))):
        key = os.path.relpath(rd, a.runs)
        if a.only and key not in a.only:
            continue
        files = [l.split("\t")[2] for l in open(os.path.join(rd, "agent.numstat")).read().splitlines() if l.strip()]
        tests = [f for f in files if "/src/test/" in f]
        if not any(f.endswith(".java") for f in tests):
            continue
        diff = os.path.abspath(os.path.join(rd, "agent.diff"))
        jobs.append((key, tests, lambda w, d=diff: sh(f"git apply --include='*/src/test/*' '{d}'", w)))
    res = {}
    with ThreadPoolExecutor(3) as ex:
        for key, r in ex.map(lambda j: run_one(j[0], j[1], j[2], tmp, a.logs), jobs):
            res[key] = r
            print(key, r["verdict"], flush=True)
    for rd in sorted(glob.glob(os.path.join(a.runs, "BUG/*/*/*"))):
        key = os.path.relpath(rd, a.runs)
        if key not in res and not a.only:
            res[key] = {"verdict": "no-tests"}
    json.dump(dict(sorted(res.items())), open(a.out, "w"), indent=1)
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
