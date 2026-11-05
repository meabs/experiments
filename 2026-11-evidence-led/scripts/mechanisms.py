"""Mechanism checks (README section 5) from the agents' commands (run.json tool_calls) and diffs, written to
results/main/mechanisms.json: skills read, whether the whole existing suite was run, whether a test was written, and
false success claims (from runs.csv). Usage: python3 -I scripts/mechanisms.py"""
import collections
import csv
import glob
import json
import os
import re

MAIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "main")
SKILLS = ("requirements-check", "build-and-verify", "self-review")


def main():
    out = collections.defaultdict(collections.Counter)
    per_run = []
    for d in sorted(glob.glob(os.path.join(MAIN, "*", "runs", "*", "*", "codex", "*"))):
        ticket, arm, _, rep = d.split(os.sep)[-4:]
        cmds = [c["text"] for c in json.load(open(os.path.join(d, "run.json"))).get("tool_calls", [])]
        joined = "\n".join(cmds)
        row = dict(ticket=ticket, arm=arm, rep=int(rep), calls=len(cmds))
        for s in SKILLS:
            row["read " + s] = bool(re.search(r"(sed|cat|head|nl|less)[^\n]*" + s + "/SKILL.md", joined))
        row["ran full suite"] = any(re.search(r"\bmvnw? [^\n]*\btest\b", c) and "-Dtest=" not in c
                                    and "skipTests" not in c for c in cmds)
        row["ran any test"] = any(re.search(r"\bmvnw?\b[^\n]*\b(test|verify|install)\b", c) and "skipTests" not in c
                                  for c in cmds)
        row["wrote a test"] = bool(re.search(r"^\+\+\+ b/.*src/test/", open(os.path.join(d, "agent.diff")).read(), re.M))
        per_run.append(row)
        out[arm]["runs"] += 1
        for k, v in row.items():
            if isinstance(v, bool):
                out[arm][k] += v
        out[arm]["calls"] += len(cmds)
    for r in csv.DictReader(open(os.path.join(MAIN, "runs.csv"))):
        out[r["arm"]]["false_claims"] += r["false_claim"] == "True"
    json.dump(dict(per_arm=out, per_run=per_run), open(os.path.join(MAIN, "mechanisms.json"), "w"), indent=1)
    for a in "VDE":
        print(a, dict(out[a]))


if __name__ == "__main__":
    main()
