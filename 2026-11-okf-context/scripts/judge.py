"""Grades each FMEA report (results/<stage>/fmea-<arm>/runs/FMEA/<arm>/codex/<rep>/fmea.md) against the answer key
(key/fmea_key.json). One judge call per report, JSON mode, from a provider other than the agent's (OpenAI):
the primary judge is google/gemini-4-argon; --judge anthropic/claude-sonnet-5.5 is the second judge (robustness).

For each key entry the judge says whether the report covers it (lenient: the same failure mode; strict: the same mode
and the same cause), which row, and for a match the quality criteria (effect on customers right; dependants named;
cause plausible for this code; detection method exists or is proposed concretely; action addresses the cause) and the
report's S, O, D. It also lists the report's rows that match no key entry (extra modes: valid, generic or wrong) and
claims about external systems, rules or the code that are in neither the code facts nor the system context (invented
facts, by class). I check the judge's matches by hand (README: every match in the pilot; in the main run every positive
and a random fifth of negatives); my corrections go in results/<stage>/judge-overrides.json.

Usage: python3 -I judge.py <stage dir> [--judge MODEL]   writes <stage dir>/judge-<model slug>.jsonl (resumable)
"""
import json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

E = Path(__file__).resolve().parent.parent
KEY = json.load(open(E / "key" / "fmea_key.json"))
CODE = (E / "key" / "code_facts.md").read_text()
CONTEXT = (E / "context" / "system-context.md").read_text()
LOCK = threading.Lock()
PROMPT = """You are grading an FMEA (failure mode and effects analysis) of a bank's accounts service, written by an AI
agent that could read the service's code, against an answer key. Be strict and literal; do not give credit for
generic statements that don't name the specific failure.

ANSWER KEY (failure modes a good FMEA of this service should contain):
%s

WHAT THE CODE STATES:
%s

THE SYSTEM CONTEXT (facts about the world around the code, from the team's wiki):
%s

THE FMEA REPORT TO GRADE:
<<<
%s
>>>

Return only JSON with these fields:
{"rows": <number of failure-mode rows or entries in the report>,
 "key": [ one object per key entry, in key order:
   {"id": "K01", "lenient": true|false, "strict": true|false, "row": "<the report's failure mode text, or empty>",
    "effect_customers": true|false, "dependants_named": ["<dependants from the key entry's list that the matched row
    names or clearly describes>"], "cause_plausible": true|false, "detection_concrete": true|false,
    "action_addresses_cause": true|false, "S": <int or null>, "O": <int or null>, "D": <int or null>} ],
 "extras": [ {"row": "<report failure mode matching no key entry>", "verdict": "valid"|"generic"|"wrong",
    "reason": "<short>"} ],
 "invented": [ {"claim": "<quote or close paraphrase>", "class": "external_system"|"rule_or_number"|"code_claim"|
    "contradicts_context", "reason": "<short>"} ]}

Rules: lenient = the report contains a row about the same failure mode (same thing going wrong), whatever words it
uses; strict = lenient and the stated cause is the key's cause or clearly the same mechanism. A row can match more
than one key entry. If lenient is false, set the other quality fields to false/[]/null. "valid" extras are real,
specific risks of this service the key missed; "generic" ones would be true of any service (e.g. "server crashes");
"wrong" ones misdescribe the system. "invented" lists only specific claims (a system, a number, a rule, a behaviour of
the code) found in neither the code facts nor the system context and not reasonable general knowledge; a claim marked
as an assumption or a question is not invented, and neither is a recommendation or a proposed change (proposing
retries where the context says there are none is advice, not a false statement). Classes: external_system = a system or team that doesn't exist here;
rule_or_number = a made-up time, limit, code or policy; code_claim = a wrong statement about what the code does;
contradicts_context = says the opposite of the system context."""


def slug(model):
    return re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")


def ask(model, report):
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    entries = [{k: e[k] for k in ("id", "mode", "cause", "effect", "dependants", "detection")} for e in KEY["entries"]]
    body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"}, "usage": {"include": True},
            "messages": [{"role": "user", "content": PROMPT % (json.dumps(entries, indent=1), CODE, CONTEXT, report)}]}
    last = None
    for _ in range(4):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=600,
                              headers={"Authorization": f"Bearer {key}"})
        except requests.RequestException as e:
            last = str(e)
            continue
        if r.status_code == 200:
            j = r.json()
            try:
                text = j["choices"][0]["message"]["content"]
                text = re.sub(r"^```(json)?|```$", "", text.strip()).strip()
                out = json.loads(text)
                ids = [k.get("id") for k in out.get("key", [])]
                if ids == [e["id"] for e in KEY["entries"]]:
                    return out, j.get("usage", {}).get("cost", 0)
                last = f"key ids {ids}"
            except (ValueError, KeyError, TypeError) as e:
                last = f"parse: {e}"
        else:
            last = f"http {r.status_code}: {r.text[:200]}"
    return {"error": last}, 0


def main(stage, model):
    stage = Path(stage)
    out = stage / f"judge-{slug(model)}.jsonl"
    done = set()
    if out.exists():
        done = {j["run"] for j in map(json.loads, out.open()) if "error" not in j}
    jobs = []
    for f in sorted(stage.glob("fmea-*/runs/FMEA/*/codex/*/fmea.md")):
        arm, rep = f.parts[-4], f.parts[-2]
        run = f"{arm}/{rep}"
        only = os.environ.get("OKFC_JUDGE_RUNS")
        if run not in done and (not only or run in only.split(",")):
            jobs.append((run, arm, int(rep), f.read_text(errors="replace")))

    def one(job):
        run, arm, rep, text = job
        label, cost = ask(model, text)
        with LOCK, out.open("a") as fh:
            fh.write(json.dumps({"run": run, "arm": arm, "rep": rep, "judge": model, "words": len(text.split()),
                                 **label, "cost": cost}) + "\n")

    with ThreadPoolExecutor(int(os.environ.get("OKFC_JUDGE_WORKERS", "6"))) as ex:
        list(ex.map(one, jobs))
    print(len(jobs), "judged by", model, "->", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    model = "google/gemini-4-argon"
    if "--judge" in args:
        i = args.index("--judge")
        model = args[i + 1]
        del args[i:i + 2]
    main(args[0], model)
