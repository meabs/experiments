"""Checks each storyboard's rendered text against the brief's checklist (key/states.json). One text-model call per run.
The model sees only the visible text of every screen (from shoot.py), never the arm, file names or process files.
For each item it answers present true/false and, if true, must quote the supporting words exactly. A "present" whose
quote is not found in the screen text (ignoring case and spacing) is set to false by this script (field
"quote_ok": false), so a present can't rest on something that isn't on a screen; I check every such case by hand,
and a random fifth of the other decisions (seed 1). Hand checks go in
<stage>/states-overrides.json ({"D1/A/1": {"D1-03": false}}).

Usage: python3 judge_states.py <stage dir> [--judge MODEL]   -> <stage dir>/states-<model slug>.jsonl (resumable)
"""
import json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

E = Path(__file__).resolve().parent.parent
KEY = json.load(open(E / "key" / "states.json"))["briefs"]
LOCK = threading.Lock()
PROMPT = """You are checking a storyboard of a UK banking app journey against a checklist. Below is the visible text
of every frame of the storyboard, in order. Be strict and literal: an item is present only if words on a screen
clearly show it. A heading alone, or a vague hint, is not enough. Do not use outside knowledge of what such an app
usually has.

CHECKLIST:
%s

SCREENS:
%s

Return only JSON: {"items": [{"id": "<item id>", "present": true|false, "quote": "<exact words copied from one
screen that show it, 5 to 25 words; empty if not present>"}]} with one object per checklist item, in order."""


def slug(model):
    return re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")


def norm(s):
    return re.sub(r"[^a-z0-9£%.]+", " ", s.lower().replace("’", "'")).strip()


def quoted(quote, n):
    # the quote counts if at least one run of four or more consecutive words from it is on a screen (models join text
    # from neighbouring elements with "..." or full stops, so the whole quote is often not contiguous)
    for frag in re.split(r"\.\.\.|…|[.!?:;]\s|\n", quote):
        f = norm(frag)
        if len(f.split()) >= 4 and f in n:
            return True
    return len(norm(quote).split()) < 4 and len(norm(quote)) >= 6 and norm(quote) in n


def ask(model, items, text):
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"}, "usage": {"include": True},
            "messages": [{"role": "user", "content": PROMPT % ("\n".join(f"- {i['id']}: {i['item']}" for i in items), text)}]}
    last = None
    for _ in range(4):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=600,
                              headers={"Authorization": f"Bearer {key}"})
        except requests.RequestException as e:
            last = str(e)
            continue
        if r.status_code != 200:
            last = f"http {r.status_code}: {r.text[:200]}"
            continue
        j = r.json()
        try:
            t = re.search(r"\{.*\}", j["choices"][0]["message"]["content"], re.S).group(0)
            out = json.loads(t)["items"]
            if [o.get("id") for o in out] == [i["id"] for i in items]:
                return out, j.get("usage", {}).get("cost", 0)
            last = "ids differ"
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            last = f"parse: {e}"
    return None, last


def main(stage, model):
    stage = Path(stage)
    out = stage / f"states-{slug(model)}.jsonl"
    done = {j["run"] for j in map(json.loads, out.open()) if "error" not in j} if out.exists() else set()
    jobs = []
    for ev in sorted(stage.glob("eval/*/*/*/eval.json")):
        brief, arm, rep = ev.parts[-4:-1]
        run = f"{brief}/{arm}/{rep}"
        e = json.loads(ev.read_text())
        seen, parts = set(), []  # a one-page storyboard repeats the same page text at every frame address: show it once
        for s in e["screens"]:
            t = s.get("text", "").strip()
            if t and s.get("text_hash") not in seen:
                seen.add(s.get("text_hash"))
                parts.append(f"--- screen {s['n']} ---\n{t}")
        text = "\n\n".join(parts)
        if run not in done:
            jobs.append((run, brief, arm, rep, text))

    def one(job):
        run, brief, arm, rep, text = job
        items = KEY[brief]
        rec = {"run": run, "brief": brief, "arm": arm, "rep": rep, "judge": model}
        if not text.strip():
            rec["items"] = [{"id": i["id"], "present": False, "quote": "", "quote_ok": True} for i in items]
            rec["cost"] = 0
        else:
            got, cost = ask(model, items, text[:60000])
            if got is None:
                rec["error"] = cost
            else:
                n = norm(text)
                for g in got:
                    g["present"] = bool(g.get("present"))
                    g["quote_ok"] = (not g["present"]) or quoted(g.get("quote", ""), n)
                    if not g["quote_ok"]:
                        g["claimed"], g["present"] = True, False
                rec["items"], rec["cost"] = got, cost
        with LOCK, out.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")

    with ThreadPoolExecutor(int(os.environ.get("DF_JUDGE_WORKERS", "6"))) as ex:
        list(ex.map(one, jobs))
    print(len(jobs), "runs checked by", model, "->", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    model = "google/gemini-4-argon"
    if "--judge" in args:
        i = args.index("--judge")
        model = args[i + 1]
        del args[i:i + 2]
    main(args[0], model)
