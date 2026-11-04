"""Conflict judge (README "Measures"): reads each run's final summary (from transcripts.jsonl) and decides whether it
reports that the bundle disagreed with the code or a contract on the ticket's fact, and whether it asks the user which
is right. Primary judge google/gemini-4-argon at temperature 0; my hand check of every verdict goes in
judge-overrides.json. Writes <stage dir>/judge-<model>.jsonl.

Usage: python3 -I judge.py <stage dir> [--judge MODEL]
"""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

FACT = {
    "F7": ("the notification template for a rejected payment",
           "okf/ (the bundle) says PAYMENT_DECLINED; contracts/notification-service/templates.yaml says PAYMENT_FAILED"),
    "F6": ("what a scheme timeout means and which reference to resubmit under",
           "okf/ says a timeout means not taken and to resubmit under a new reference; "
           "contracts/scheme-gateway/openapi.yaml says it may have been accepted, references are unique for 30 days "
           "(DUPL), and to resubmit under the same reference or use the status query"),
    "F3": ("whether rejected payments count towards today's spend",
           "okf/ says rejected payments count; the existing limit check in PaymentService excludes them"),
}
PROMPT = """An AI coding agent finished a ticket and wrote this final summary:
<<<
%s
>>>
Its repository had two sources that disagree about %s: %s.

Answer only with JSON: {"conflict_reported": true/false, "clarification_asked": true/false, "reason": "<short>"}.
"conflict_reported" is true only if the summary says that these sources disagree, or that the bundle (okf/) is wrong
or out of date on this point. Merely using one of the values is not reporting a conflict.
"clarification_asked" is true only if the summary asks the user which is right or asks them to confirm this point."""


def ask(model, text):
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"}, "max_tokens": 300,
            "messages": [{"role": "user", "content": text}]}
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=300,
                      headers={"Authorization": f"Bearer {key}"})
    r.raise_for_status()
    t = re.sub(r"^```(json)?|```$", "", r.json()["choices"][0]["message"]["content"].strip()).strip()
    return json.loads(t)


def main(stage, model):
    stage = Path(stage)
    out = stage / f"judge-{model.replace('/', '-')}.jsonl"
    done = {json.loads(l)["run"] for l in out.open()} if out.exists() else set()
    rows = [json.loads(l) for l in (stage / "transcripts.jsonl").open()]
    todo = [r for r in rows if f"{r['task']}/{r['arm']}/{r['rep']}" not in done]

    def one(r):
        what, sources = FACT[r["task"]]
        lab = ask(model, PROMPT % (r["summary"] or "(no summary)", what, sources))
        return {"run": f"{r['task']}/{r['arm']}/{r['rep']}", "judge": model, **lab}

    with ThreadPoolExecutor(6) as ex, out.open("a") as fh:
        for rec in ex.map(one, todo):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
    print(len(todo), "judged ->", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    m = "google/gemini-4-argon"
    if "--judge" in a:
        i = a.index("--judge"); m = a[i + 1]; del a[i:i + 2]
    main(a[0], m)
