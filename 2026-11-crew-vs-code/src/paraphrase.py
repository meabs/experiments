"""Adds the level-6 paraphrases to cases/paraphrased.json (the first 32 are copied unchanged from need-an-agent),
with need-an-agent's prompt and model (google/gemini-3.1-flash-lite, not under test). Checked by hand afterwards:
same order numbers, items, requests and preferences, nothing added; corrections, if any, are listed in README.md.
Usage: python3 -I paraphrase.py
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base  # noqa: E402,F401
from crewcases import L6  # noqa: E402
from llm import LLM, parse_json  # noqa: E402

PROMPT = open(os.path.join(base.NA, "paraphrase.py")).read().split('PROMPT = """')[1].split('"""')[0]
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cases", "paraphrased.json")
out = json.load(open(path))
llm = LLM("google/gemini-3.1-flash-lite")
for c in L6:
    m = llm.chat([{"role": "system", "content": PROMPT},
                  {"role": "user", "content": f"Subject: {c['subject']}\n\n{c['body']}"}], json_mode=True)
    d = parse_json(m.get("content"))
    assert d and d.get("body"), c["id"]
    out[c["id"]] = {"subject": d.get("subject") or c["subject"], "body": d["body"]}
json.dump(out, open(path, "w"), indent=1, ensure_ascii=False)
print(path, llm.usage())
