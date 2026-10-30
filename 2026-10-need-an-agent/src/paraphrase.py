"""Writes cases/paraphrased.json: a second wording of every email, by a model that is not under test
(google/gemini-3.1-flash-lite, via OpenRouter), so that the plain-code rules (written by me after reading the
original wording) are also judged on wording they haven't seen. Each paraphrase is then checked by hand: same order
numbers, items, requests and preferences, nothing added. Hand corrections, if any, are listed in README.md.
Usage: python3 -I paraphrase.py   (overwrites cases/paraphrased.json)
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases import CASES  # noqa: E402
from llm import LLM, parse_json  # noqa: E402

PROMPT = """Rewrite this customer email to an online homeware shop as a different customer might write it. Use
different words and sentence structure; you may make it more casual, more formal or a little rambling, and add a
greeting or sign-off. Keep every fact exactly: order numbers written exactly as they are (same characters), the items,
what the customer wants, and any preference they state. Don't add new requests, facts or questions, and don't drop
any. Return only JSON: {"subject": "...", "body": "..."}"""

llm = LLM("google/gemini-3.1-flash-lite")
out = {}
for c in CASES:
    m = llm.chat([{"role": "system", "content": PROMPT},
                  {"role": "user", "content": f"Subject: {c['subject']}\n\n{c['body']}"}], json_mode=True)
    d = parse_json(m.get("content"))
    assert d and d.get("body"), c["id"]
    out[c["id"]] = {"subject": d.get("subject") or c["subject"], "body": d["body"]}
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cases", "paraphrased.json")
json.dump(out, open(path, "w"), indent=1, ensure_ascii=False)
print(path, llm.usage())
