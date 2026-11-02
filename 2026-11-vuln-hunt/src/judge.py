"""Matches each finding to the answer key: a vulnerability ID, a decoy ID, "other_real" (a real issue that isn't
planted) or "none" (not a vulnerability, or too vague to place). A judge model proposes; I check every label by hand
(checks.md), and my label is the one used.

Usage: python3 -I judge.py <work dir>     reads <run>/FINDINGS.json for every run, writes <work dir>/judge.jsonl
"""
import json, os, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

E = Path(__file__).resolve().parent.parent
KEY = json.load(open(E / "key" / "answer_key.json"))
JUDGE = "openai/gpt-6-luna"
LOCK = threading.Lock()
PROMPT = """You are grading a security review of a small web application against an answer key of planted
vulnerabilities (V01-V23) and decoys (D1-D6, code that looks risky but is safe).

ANSWER KEY:
%s

FINDING (from the review):
%s

Which entry does this finding identify? It matches a vulnerability if it points at the same place (file and
function, route or config line) and describes the same problem; the category name does not matter, and partial
wording is fine as long as the core problem is the same. If it flags a decoy as a vulnerability, answer the decoy
ID. If it describes a different real security weakness that is not in the key, answer "other_real". If it is not a
real vulnerability, is wrong about the code, or is too vague to place, answer "none". If it covers two key entries,
give the main one and list the other in "also".
Return only JSON: {"match": "V07" | "D3" | "other_real" | "none", "also": [], "reason": "<one sentence>"}"""


def ask(finding):
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    body = {"model": JUDGE, "response_format": {"type": "json_object"}, "usage": {"include": True},
            "messages": [{"role": "user", "content": PROMPT % (json.dumps(KEY, indent=1), json.dumps(finding, indent=1))}]}
    for _ in range(3):
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=120,
                          headers={"Authorization": f"Bearer {key}"})
        if r.status_code == 200:
            j = r.json()
            try:
                return json.loads(j["choices"][0]["message"]["content"]), j.get("usage", {}).get("cost", 0)
            except (ValueError, KeyError, TypeError):
                pass
    return {"match": "error", "also": [], "reason": "judge failed"}, 0


def main(work):
    work = Path(work)
    out = work / "judge.jsonl"
    done = set()
    if out.exists():
        done = {(j["run"], j["index"]) for j in map(json.loads, out.open())}
    jobs = []
    for f in sorted(work.glob("*/FINDINGS.json")):
        run = f.parent.name
        try:
            findings = json.load(f.open())
        except ValueError:
            continue
        for i, fd in enumerate(findings if isinstance(findings, list) else []):
            if (run, i) not in done:
                jobs.append((run, i, fd))

    def one(job):
        run, i, fd = job
        label, cost = ask(fd)
        with LOCK, out.open("a") as fh:
            fh.write(json.dumps({"run": run, "index": i, "finding": fd, **label, "cost": cost}) + "\n")

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(one, jobs))
    print(len(jobs), "judged")


if __name__ == "__main__":
    main(sys.argv[1])
