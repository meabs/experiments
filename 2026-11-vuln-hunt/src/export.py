"""Copy the parts of a main run that the analysis and the report need into results/main.

Usage: python3 -I export.py <work dir>
Per run: meta.json, FINDINGS.json, usage.json (Strands arms) and tools.jsonl (every tool call; for Codex, its shell
commands from events.jsonl). Plus key.json and judge.jsonl. Not copied: model transcripts, Codex event streams, the
app copies. Local paths are replaced with <ws> and ~.
"""
import json, os, re, shutil, sys
from pathlib import Path

E = Path(__file__).resolve().parent.parent
work, out = Path(sys.argv[1]), E / "results" / "main"
HOME = os.path.expanduser("~")


def clean(s, run):
    s = s.replace(str(work / run / "ws"), "<ws>").replace(str(work / run), "<run>")
    return re.sub(r"/tmp/[^\s\"']*", "<tmp>", s.replace(HOME, "~"))


def main():
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in ("key.json", "judge.jsonl"):
        shutil.copy(work / name, out / name)
    for run in sorted(json.load(open(work / "key.json"))):
        src, dst = work / run, out / run
        dst.mkdir()
        for name in ("meta.json", "FINDINGS.json", "usage.json", "tools.jsonl"):
            if (src / name).exists():
                (dst / name).write_text(clean((src / name).read_text(), run))
        if (src / "events.jsonl").exists():
            with open(dst / "tools.jsonl", "w") as f:
                for line in open(src / "events.jsonl"):
                    e = json.loads(line)
                    it = e.get("item") or {}
                    if e.get("type") == "item.completed" and it.get("type") in ("command_execution", "file_change"):
                        row = {"agent": "codex", "tool": it["type"],
                               "input": it.get("command") or [c.get("path") for c in it.get("changes", [])],
                               "exit_code": it.get("exit_code")}
                        f.write(clean(json.dumps(row), run) + "\n")
    print(f"exported to {out}")


if __name__ == "__main__":
    main()
