"""Reads each run's Codex event log (raw.out.gz) and records how the run used the context and explored the code
(README "Detailed analysis plan", part 3). Codex loads AGENTS.md into the prompt itself, so arm C's section is always
in context; for arm B the question is whether and when the run opened okf/.

Per run: commands; okf files opened (B) and the position of the first okf read; files opened under src/; searches
(rg/grep/find); commands before the first edit (feature tasks: the first file change; FMEA: the first change to
docs/fmea.md); whether the run ran the tests; tokens. Writes <stage dir>/transcripts.jsonl.
Usage: python3 -I transcripts.py <stage dir>
"""
import gzip, json, re, sys
from pathlib import Path

OKF = re.compile(r"okf/(index|system|architecture|context)\.md")
SRC = re.compile(r"src/[\w/.-]+\.(java|sql|yml)")


def one(run_dir):
    events = []
    f = run_dir / "raw.out.gz"
    with (gzip.open(f, "rt", errors="replace") if f.exists() else open(run_dir / "raw.out", errors="replace")) as fh:
        for line in fh:
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    cmds, okf_first, edit_first, okf_files, src_files, searches, tests = [], None, None, set(), set(), 0, False
    for e in events:
        it = e.get("item", {})
        if e.get("type") != "item.completed":
            continue
        if it.get("type") == "command_execution":
            c = it.get("command", "")
            cmds.append(c)
            hits = set(OKF.findall(c))
            if re.search(r"\bokf\b", c) and not hits and re.search(r"(cat|sed|head|rg|grep|ls|find)\b", c):
                hits.add("(listing or search)")
            if hits:
                okf_files |= hits
                if okf_first is None:
                    okf_first = len(cmds)
            src_files |= set(m.group(0) for m in SRC.finditer(c))
            if re.search(r"\b(rg|grep|find)\b", c):
                searches += 1
            if re.search(r"\bmvn\b.*\btest\b", c):
                tests = True
        elif it.get("type") == "file_change" and edit_first is None:
            paths = [ch.get("path", "") for ch in it.get("changes", [])]
            if run_dir.parts[-4] != "FMEA" or any(p.endswith("docs/fmea.md") for p in paths):
                edit_first = len(cmds)
    # The FMEA may be written by a shell command instead of a file change.
    if edit_first is None and run_dir.parts[-4] == "FMEA":
        for i, c in enumerate(cmds):
            if "docs/fmea.md" in c and re.search(r"(>|tee|cat <<|python)", c):
                edit_first = i
                break
    run = json.load(open(run_dir / "run.json"))
    return {"task": run_dir.parts[-4], "arm": run_dir.parts[-3], "rep": int(run_dir.parts[-1]),
            "commands": len(cmds), "okf_read": bool(okf_files), "okf_files": sorted(okf_files),
            "okf_first_command": okf_first, "src_files_opened": len(src_files), "searches": searches,
            "commands_before_first_edit": edit_first, "ran_tests": tests, "status": run.get("status"),
            "seconds": run.get("seconds"), "tokens": run.get("tokens")}


def main(stage):
    stage = Path(stage)
    rows = [one(p.parent) for p in sorted(list(stage.glob("*/runs/*/*/codex/*/raw.out.gz")) + list(stage.glob("*/runs/*/*/codex/*/raw.out")))]
    with open(stage / "transcripts.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(len(rows), "runs ->", stage / "transcripts.jsonl")


if __name__ == "__main__":
    main(sys.argv[1])
