"""Retrospective process measures from the agents' event logs: test-file-first and evidence of genuine TDD.

test-file-first (the preregistered H5 measure, renamed): the first edit under src/test comes before the first edit
under src/main, counting only edits made through the agent's edit tool (Codex file_change, Cursor edit).

tdd (new, retrospective), from the full timeline including shell-made edits and test runs:
  tdd-confirmed     a test file was edited before any production file; a test run between the two failed with a
                    test failure in a test class this run changed (not a compile error); after the first production
                    edit a later test run passed.
  test-file-first   test file edited first, but the red-then-green evidence above is missing from complete logs.
  impl-first        a production file was edited before any test file.
  no-test-edits     no test file was edited.
  unknown           the logs cannot settle it: a subagent ran, a shell command edited files whose paths cannot be
                    read, or the decisive test run's output does not say which class failed.

Usage: python3 -I process.py <runs dir> <out json>
"""
import glob, gzip, json, os, re, sys

MVN = re.compile(r"(^|[\s/;&|('\"])(mvn|mvnw)\b")
GOALS = re.compile(r"\b(test|verify|install|package)\b")
SKIP = re.compile(r"-DskipTests|-Dmaven\.test\.skip=true")
FAIL_IN = re.compile(r"<<< (?:FAILURE|ERROR)! - in ([\w.$]+)")
FAIL_CASE = re.compile(r"\[ERROR\]\s+(?:Failures|Errors):?\s*$|\[ERROR\]\s+([A-Z][\w$]*)\.\w+[:\s]")
RUN_LINE = re.compile(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+)")
ANSI = re.compile(r"\x1b\[[0-9;]*m|\[[0-9;]*m(?=\S)")
DTEST = re.compile(r"-Dtest=['\"]?([\w$.,#*]+)")
JAVA = r"[\w./~$-]+\.java"
SHELL_EDITS = [
    re.compile(r">>?\s*['\"]?(" + JAVA + ")"),
    re.compile(r"\btee\s+(?:-a\s+)?['\"]?(" + JAVA + ")"),
    re.compile(r"\b(?:sed|perl)\s+-[a-zA-Z]*i\S*\s[^|;&]*?(" + JAVA + ")"),
    re.compile(r"\*\*\* (?:Add|Update|Delete) File: (\S+)"),
    re.compile(r"\b(?:mv|cp)\s+\S+\s+['\"]?(" + JAVA + ")"),
]
OPAQUE_EDIT = re.compile(r"open\([^)]*['\"]w|write_text\(|\bgit apply\b|\bpatch\s+-p|Files\.write")


def kind(path):
    return "test" if "/src/test/" in path else "main" if "/src/main/" in path else None


def is_test_run(cmd):
    return bool(MVN.search(cmd)) and bool(GOALS.search(cmd)) and not SKIP.search(cmd)


def test_outcome(exit_code, output, cmd=""):
    """green, red (with failing classes), compile-error, or unknown.

    Failing classes come from surefire's lines; if the output has none but says "There are test failures", the
    failure is attributed to the classes named in -Dtest, the only tests that command ran."""
    output = ANSI.sub("", output)
    if "COMPILATION ERROR" in output or "cannot find symbol" in output:
        return "compile-error", []
    failing = {m.split(".")[-1] for m in FAIL_IN.findall(output)}
    failing |= {m for m in FAIL_CASE.findall(output) if m}
    bad = any(int(f) + int(e) for _, f, e in RUN_LINE.findall(output))
    if not failing and "There are test failures" in output:
        m = DTEST.search(cmd)
        if m:
            failing = {c.split("#")[0].split(".")[-1] for c in m.group(1).split(",") if c}
        bad = True
    if exit_code not in (0, None) and (bad or failing):
        return "red", sorted(failing)
    if exit_code == 0:
        return "green", []
    return "unknown", []


def shell_edits(cmd):
    """(paths edited, opaque) for one shell command."""
    paths = set()
    for rx in SHELL_EDITS:
        paths |= set(rx.findall(cmd))
    paths = {p for p in paths if kind(p)}
    opaque = bool(OPAQUE_EDIT.search(cmd)) and ("src/" in cmd)
    return sorted(paths), opaque


def events_codex(lines):
    ev = []
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        it = e.get("item") or {}
        if e.get("type") != "item.completed":
            continue
        if it.get("type") == "file_change":
            for c in it.get("changes", []):
                ev.append({"k": "edit", "path": c["path"], "via": "tool"})
        elif it.get("type") == "command_execution":
            ev += _shell(it.get("command", ""), it.get("exit_code"), it.get("aggregated_output", ""))
    return ev


def events_cursor(lines):
    ev = []
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") != "tool_call" or e.get("subtype") != "completed":
            continue
        tc = e.get("tool_call", {})
        name = next(iter(tc), "")
        body = tc.get(name, {})
        if name == "editToolCall":
            ev.append({"k": "edit", "path": body.get("args", {}).get("path", ""), "via": "tool"})
        elif name == "shellToolCall":
            r = body.get("result", {})
            r = r.get("success") or r.get("failure") or {}
            ev += _shell(body.get("args", {}).get("command", ""), r.get("exitCode"),
                         (r.get("stdout") or "") + (r.get("stderr") or ""))
        elif name in ("taskToolCall", "task") or "task" in name.lower():
            ev.append({"k": "subagent"})
    return ev


def _shell(cmd, code, out):
    ev = []
    paths, opaque = shell_edits(cmd)
    ev += [{"k": "edit", "path": p, "via": "shell"} for p in paths]
    if opaque:
        ev.append({"k": "opaque-edit"})
    if is_test_run(cmd):
        o, failing = test_outcome(code, out, cmd)
        ev.append({"k": "test", "outcome": o, "failing": failing})
    return ev


def test_file_first(ev):
    """Preregistered measure: tool edits only. True/False, or None if there is not both a test and a main edit."""
    tool = [kind(e["path"]) for e in ev if e["k"] == "edit" and e["via"] == "tool"]
    if "test" not in tool or "main" not in tool:
        return None
    return tool.index("test") < tool.index("main")


def classify_tdd(ev, own_test_classes):
    """Pure function: see module docstring. Returns (verdict, reason)."""
    edits = [(i, kind(e["path"])) for i, e in enumerate(ev) if e["k"] == "edit" and kind(e["path"])]
    t0 = next((i for i, k in edits if k == "test"), None)
    m0 = next((i for i, k in edits if k == "main"), None)
    uncertain = [e["k"] for e in ev if e["k"] in ("subagent", "opaque-edit")]
    why_unknown = "subagent" if "subagent" in uncertain else "unreadable shell edit"
    if t0 is None:
        return ("unknown", why_unknown) if uncertain else ("no-test-edits", "")
    if m0 is not None and m0 < t0:
        return ("unknown", why_unknown) if uncertain else ("impl-first", "")
    stop = m0 if m0 is not None else len(ev)
    runs = [e for e in ev[t0:stop] if e["k"] == "test"]
    reds = [e for e in runs if e["outcome"] == "red"]
    own_red = any(set(e["failing"]) & own_test_classes for e in reds)
    unattributed = any(not e["failing"] for e in reds) or any(e["outcome"] == "unknown" for e in runs)
    green_after = m0 is not None and any(e["k"] == "test" and e["outcome"] == "green" for e in ev[m0:])
    if uncertain:
        return "unknown", why_unknown
    if own_red and green_after:
        return "tdd-confirmed", ""
    if unattributed and not own_red:
        return "unknown", "test run output does not name the failing class"
    if m0 is None:
        reason = "no production edit"
    elif not runs:
        reason = "no test run before the fix"
    elif not reds:
        reason = "compile error only" if any(e["outcome"] == "compile-error" for e in runs) else "tests passed before the fix"
    elif not own_red:
        reason = "only other classes failed"
    else:
        reason = "no passing test run after the fix"
    return "test-file-first", reason


def main():
    runs, out = sys.argv[1], sys.argv[2]
    res = {}
    for f in sorted(glob.glob(os.path.join(runs, "*/*/*/*/run.json"))):
        rd = os.path.dirname(f)
        key = os.path.relpath(rd, runs)
        agent = key.split("/")[2]
        raw = os.path.join(rd, "raw.out")
        fh = open(raw) if os.path.exists(raw) else gzip.open(raw + ".gz", "rt")
        ev = (events_codex if agent == "codex" else events_cursor)(fh)
        numstat = [l.split("\t")[2] for l in open(os.path.join(rd, "agent.numstat")).read().splitlines() if l.strip()]
        own = {os.path.basename(p)[:-5] for p in numstat if "/src/test/" in p and p.endswith(".java")}
        tool_edits = [e for e in ev if e["k"] == "edit" and e["via"] == "tool"]
        res[key] = {
            "test_file_first": test_file_first(ev),
            "tdd": classify_tdd(ev, own)[0],
            "tdd_reason": classify_tdd(ev, own)[1],
            "test_runs": sum(e["k"] == "test" for e in ev),
            "red_runs": sum(e["k"] == "test" and e["outcome"] == "red" for e in ev),
            "shell_edits": sum(e["k"] == "edit" and e["via"] == "shell" for e in ev),
            "opaque_edits": sum(e["k"] == "opaque-edit" for e in ev),
            "subagents": sum(e["k"] == "subagent" for e in ev),
            "edits_seen": len(tool_edits) > 0 or any(e["k"] == "edit" for e in ev),
            "changed_files": len(numstat),
        }
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
