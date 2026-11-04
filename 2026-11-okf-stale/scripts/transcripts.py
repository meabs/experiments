"""Reads each run's Codex event log (raw.out.gz) and records how the run decided (README "Measures" and "Detailed
analysis plan", part 3).

Per run: commands; okf files opened and the position of the first okf read; the authoritative source for the ticket
(F7: contracts/notification-service/templates.yaml; F6: contracts/scheme-gateway/openapi.yaml; F3: PaymentService.java)
and the position of its first read; any contracts/ file opened; whether the run ran `date`; whether its messages
mention the bundle's freshness fields; files opened under src/; searches; commands before the first edit; whether it
ran the tests; tokens; and the final summary (the agent's last message), for the conflict judge.
Writes <stage dir>/transcripts.jsonl.
Usage: python3 -I transcripts.py <stage dir>
"""
import gzip, json, re, sys
from pathlib import Path

OKF = re.compile(r"okf/(index|system|architecture|context)\.md")
SRC = re.compile(r"src/[\w/.-]+\.(java|sql|yml)")
TRUTH_SRC = {"F7": re.compile(r"contracts/notification-service/templates\.yaml|contracts/notification-service\b"),
             "F6": re.compile(r"contracts/scheme-gateway/openapi\.yaml|contracts/scheme-gateway\b"),
             "F3": re.compile(r"PaymentService\.java")}
CONTRACTS = re.compile(r"\bcontracts\b")
FRESH = re.compile(r"stale_after|verified|out of date|outdated|stale|2026-03-03|2026-06-01", re.I)


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
    task = run_dir.parts[-4]
    truth_first, contracts, ran_date, messages = None, False, False, []
    for e in events:
        it = e.get("item", {})
        if e.get("type") != "item.completed":
            continue
        if it.get("type") == "agent_message":
            messages.append(it.get("text", ""))
        if it.get("type") == "command_execution":
            c = it.get("command", "")
            cmds.append(c)
            if truth_first is None and TRUTH_SRC[task].search(c):
                truth_first = len(cmds)
            contracts = contracts or bool(CONTRACTS.search(c))
            ran_date = ran_date or bool(re.search(r"(^|[;&|\s'\"])date(\s|$|['\";])", c))
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
            edit_first = len(cmds)
    run = json.load(open(run_dir / "run.json"))
    return {"task": run_dir.parts[-4], "arm": run_dir.parts[-3], "rep": int(run_dir.parts[-1]),
            "commands": len(cmds), "okf_read": bool(okf_files), "okf_files": sorted(okf_files),
            "okf_first_command": okf_first, "truth_source_first_command": truth_first,
            "truth_source_before_edit": truth_first is not None and (edit_first is None or truth_first <= edit_first),
            "opened_contracts": contracts, "ran_date": ran_date,
            "mentions_freshness": any(FRESH.search(m) for m in messages),
            "summary": messages[-1] if messages else "", "src_files_opened": len(src_files), "searches": searches,
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
