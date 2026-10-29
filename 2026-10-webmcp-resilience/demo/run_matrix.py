"""The demo: for every version of every app, does an ordinary check catch the bug, and does WebMCP Resilience?

Versions: the buggy original, the reference fix, the planted wrong fixes (wrong-fixes/<app>/<name>) and real agent fixes
(demo/agent-fixes/<app>--<who>.diff, from the pilot runs). For each version:
- ground truth: the full hidden test suite (hidden/<app>.py, plain Playwright, independent of the tool);
- ordinary check: the hidden suite's first two cases only, one person or one assistant call at normal speed;
- WebMCP Resilience: every scenario in demo/scenarios/<app>/ (check_tool.py); it catches the version if any scenario
  reports an invariant violation.
Writes demo/results.json. Usage: python3 -I demo/run_matrix.py [app ...]
"""
import glob, importlib, io, json, os, shutil, subprocess, sys, tempfile
from contextlib import redirect_stdout

D = os.path.dirname(os.path.abspath(__file__))
E = os.path.dirname(D)
sys.path.insert(0, os.path.join(E, "hidden"))
sys.path.insert(0, D)
import harness  # noqa: E402
import check_tool  # noqa: E402

RUNS = 3
APPS = ["double-add", "last-seat", "lost-update", "half-saved", "charge-no-order", "stale-quantity"]


def app_copy(app, overlay=None, diff=None):
    tmp = tempfile.mkdtemp()
    ws = os.path.join(tmp, "app")
    shutil.copytree(os.path.join(E, os.environ.get("WEBMCP_APPS", "apps"), app), ws)
    if overlay:
        shutil.copytree(overlay, ws, dirs_exist_ok=True)
    if diff:
        subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
        subprocess.run(["git", "apply", "--whitespace=nowarn", diff], cwd=ws, check=True)
        shutil.rmtree(os.path.join(ws, ".git"))
    return tmp, ws


def hidden(app, ws, first=None):
    mod = importlib.import_module(app.replace("-", "_"))
    cases = mod.CASES[:first] if first else mod.CASES
    buf = io.StringIO()
    with redirect_stdout(buf):
        harness.run(ws, cases)
    r = json.loads(buf.getvalue())
    return {"passed": r["passed"], "total": r["total"], "failed": [c["case"] for c in r["cases"] if not c["passed"]]}


def versions(app):
    yield "original", "buggy original", {}
    yield "reference", "reference fix", {"overlay": os.path.join(E, "reference", app)}
    for w in sorted(glob.glob(os.path.join(E, "wrong-fixes", app, "*"))):
        yield f"wrong:{os.path.basename(w)}", "planted wrong fix", {"overlay": w}
    for d in sorted(glob.glob(os.path.join(D, "agent-fixes", f"{app}--*.diff"))):
        yield f"agent:{os.path.basename(d)[len(app) + 2:-5]}", "agent fix", {"diff": d}


def main(apps):
    out_path = os.path.join(D, os.environ.get("WEBMCP_RESULTS", "results.json"))
    results = json.load(open(out_path)) if os.path.exists(out_path) else {}
    for app in apps:
        for vid, kind, src in versions(app):
            tmp, ws = app_copy(app, **src)
            try:
                truth = hidden(app, ws)
                ordinary = hidden(app, ws, first=2)
                tools = [check_tool.check(app, ws) for _ in range(RUNS)]  # timing-dependent: run each check 3 times
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            row = {"app": app, "version": vid, "kind": kind,
                   "buggy": truth["passed"] < truth["total"], "hidden": truth,
                   "ordinary_catches": ordinary["passed"] < ordinary["total"], "ordinary": ordinary,
                   "tool_catch_runs": sum(any(v["code"] == "invariant_violation" for v in t.values()) for t in tools),
                   "tool_runs": RUNS,
                   "tool_errors": sorted({k for t in tools for k, v in t.items() if not v["pass"] and v["code"] != "invariant_violation"}),
                   "tool": tools}
            row["tool_catches"] = row["tool_catch_runs"] > 0
            results[f"{app}/{vid}"] = row
            print(f"{app:16} {vid:40} buggy={row['buggy']!s:5} ordinary={row['ordinary_catches']!s:5} "
                  f"tool={row['tool_catch_runs']}/{RUNS} errors={row['tool_errors']}", flush=True)
            json.dump(results, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:] or APPS)
