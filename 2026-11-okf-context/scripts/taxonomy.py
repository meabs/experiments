"""Failure taxonomy for failed feature runs (README, section 1): a judge model labels each failed run from the ticket,
the failed hidden tests and the agent's diff, into fixed categories; my own labels are in MINE below; Cohen's kappa
between the two is written with the table to results/<stage>/taxonomy.md.

Usage: python3 -I taxonomy.py <stage dir> [--judge MODEL]
"""
import gzip, json, re, sys
from collections import Counter
from pathlib import Path

import requests

E = Path(__file__).resolve().parent.parent
CATS = ["integration rule wrong", "ticket behaviour wrong", "existing test broken", "incomplete change", "wrong file",
        "build failure"]
RULES = ["DUPL on resubmission treated as a refusal", "new scheme reference on resubmission",
         "wrong notification template name", "full account number in a notification", "other"]
# My labels, from reading each failed run's diff and transcript (2026-11-04).
MINE = {**{f"F6/{a}/{r}": ("integration rule wrong", "DUPL on resubmission treated as a refusal")
           for a, r in (("A", 1), ("A", 3), ("A", 4), ("A", 5), ("C", 2), ("C", 4))},
        **{f"F7/A/{r}": ("integration rule wrong", "wrong notification template name") for r in range(1, 6)}}
PROMPT = """An AI agent was given this ticket for a Java service:
<<<
%s
>>>
Its change failed these hidden tests (name: message):
%s
Its diff:
<<<
%s
>>>
Classify the failure. Return only JSON: {"category": one of %s, "rule": one of %s, "reason": "<short>"}.
"integration rule wrong" means the change breaks a rule about how an external system behaves (its codes, references,
templates or timeouts); "rule" names which rule, or "other"."""


def ask(model, text):
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
            "max_tokens": 400, "messages": [{"role": "user", "content": text}]}
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=300,
                      headers={"Authorization": f"Bearer {key}"})
    r.raise_for_status()
    t = re.sub(r"^```(json)?|```$", "", r.json()["choices"][0]["message"]["content"].strip()).strip()
    return json.loads(t)


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(a) | set(b)) / n / n
    return po, (None if pe == 1 else (po - pe) / (1 - pe))


def main(stage, model):
    stage = Path(stage)
    out = stage / "taxonomy-judge.jsonl"
    done = {json.loads(l)["run"]: json.loads(l) for l in out.open()} if out.exists() else {}
    for g in sorted(stage.glob("feat-*/runs/*/*/codex/*/grade.json")):
        grade = json.load(open(g))
        task, arm, rep = g.parts[-5], g.parts[-4], g.parts[-2]
        run = f"{task}/{arm}/{rep}"
        if grade["pass"] or run in done:
            continue
        d = next(g.parent.glob("agent.diff*"))
        diff = (gzip.open(d, "rt") if d.suffix == ".gz" else open(d)).read()[:15000]
        text = PROMPT % ((E / "tasks" / task / "prompt.md").read_text(), "\n".join(grade["failed"]), diff,
                         json.dumps(CATS), json.dumps(RULES))
        lab = ask(model, text)
        done[run] = {"run": run, "judge": model, **lab}
        with out.open("a") as fh:
            fh.write(json.dumps(done[run]) + "\n")
    runs = sorted(done)
    rows = [f"| {r} | {MINE[r][0]} | {MINE[r][1]} | {done[r].get('category')} | {done[r].get('rule')} |" for r in runs]
    po_c, k_c = kappa([MINE[r][0] for r in runs], [done[r].get("category") for r in runs])
    po_r, k_r = kappa([MINE[r][1] for r in runs], [done[r].get("rule") for r in runs])
    fmt = lambda k: "undefined (every label is the same, so chance agreement is 100%)" if k is None else f"{k:.2f}"
    md = ["# Failure taxonomy of failed feature runs", "",
          f"Labelled by me (from the diff and transcript) and by `{model}` (from the ticket, failed tests and diff).", "",
          "| Run | Category (me) | Rule (me) | Category (judge) | Rule (judge) |", "| --- | --- | --- | --- | --- |", *rows, "",
          f"Agreement on category: {po_c:.0%}; Cohen's kappa {fmt(k_c)}.",
          f"Agreement on rule: {po_r:.0%}; Cohen's kappa {fmt(k_r)}.", ""]
    (stage / "taxonomy.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    a = sys.argv[1:]
    m = "google/gemini-4-argon"
    if "--judge" in a:
        i = a.index("--judge"); m = a[i + 1]; del a[i:i + 2]
    main(a[0], m)
