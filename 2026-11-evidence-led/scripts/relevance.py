"""Reads the two test runs made by relevance.sh and writes the verdict as JSON.

Usage: relevance.py <out.json> <classes|none> <with dir> <original dir> <log dir> <modules> <files>
"""
import glob, json, os, re, sys
import xml.etree.ElementTree as ET

out, classes, with_dir, orig_dir, logs, modules, files = sys.argv[1:8]


def results(root, cls, log):
    """Counts tests, failures and errors in the surefire reports for the agent's classes, and whether the build compiled."""
    r = dict(tests=0, failures=0, errors=0, skipped=0, compiled=True, exit=None, failing=[])
    text = open(os.path.join(logs, log), errors="replace").read() if os.path.exists(os.path.join(logs, log)) else ""
    rc = os.path.join(logs, log + ".rc")
    r["exit"] = int(open(rc).read().strip() or -1) if os.path.exists(rc) else None
    if "COMPILATION ERROR" in text or re.search(r"Compilation failure", text):
        r["compiled"] = False
    for x in glob.glob(os.path.join(root, "**", "target", "surefire-reports", "TEST-*.xml"), recursive=True):
        name = os.path.basename(x)[5:-4].rsplit(".", 1)[-1]
        if name not in cls:
            continue
        s = ET.parse(x).getroot()
        for k in ("tests", "failures", "errors", "skipped"):
            r[k] += int(s.get(k, 0))
        for tc in s.iter("testcase"):
            if tc.find("failure") is not None or tc.find("error") is not None:
                r["failing"].append(f"{name}.{tc.get('name')}")
    return r


v = dict(files=[f for f in files.split("\n") if f], classes=[] if classes == "none" else classes.split(","))
if not v["classes"]:
    v.update(relevant=False, reason="no test of its own")
else:
    cls = set(v["classes"])
    w = results(with_dir, cls, "relevance-change.log")
    o = results(orig_dir, cls, "relevance-original.log")
    v.update(with_change=w, original=o)
    passes_with = w["compiled"] and w["tests"] > 0 and w["failures"] + w["errors"] == 0
    fails_orig = (not o["compiled"]) or o["failures"] + o["errors"] > 0
    orig_ran = o["exit"] is not None and (o["tests"] > 0 or not o["compiled"])
    v["passes_with_change"] = passes_with
    v["original_ran"] = orig_ran
    v["fails_on_original"] = fails_orig
    v["original_compile_error"] = not o["compiled"]
    v["relevant"] = passes_with and fails_orig and orig_ran
    if w["exit"] is None:
        v["reason"] = "check error: the run with the change did not happen"
    elif not w["compiled"] or w["tests"] == 0:
        v["reason"] = "its tests did not compile or run with the change"
    elif not passes_with:
        v["reason"] = "its tests fail with the change: " + ", ".join(w["failing"][:5])
    elif not orig_ran:
        v["reason"] = "check error: the run on the original code did not happen"
    elif not fails_orig:
        v["reason"] = "its tests also pass without the change"
    else:
        v["reason"] = "relevant"
json.dump(v, open(out, "w"), indent=1)
print(json.dumps({k: v[k] for k in ("relevant", "reason")}))
