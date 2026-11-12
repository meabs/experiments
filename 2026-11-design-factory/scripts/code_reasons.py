"""Why did the judges choose what they chose? Codes each judge's one-sentence reason (from judge_pairs.py, original
and cropped runs) into a fixed set of themes with a model that sees only the sentence and which design won
(not the arm), then counts themes by the arm that won. Descriptive; the coder is a model, so counts are approximate.
Usage: python3 code_reasons.py <stage dir>  -> <stage>/reasons-coded.jsonl, <stage>/analysis-reasons.md"""
import json, re, sys, threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests

THEMES = {
    "finished_look": "looks polished, finished, like a real banking app",
    "identity": "distinctive, branded, deliberate look (or the opposite: generic, plain, default)",
    "hierarchy": "clear visual hierarchy, what matters is obvious",
    "journey_complete": "complete journey, states, branches, end to end (or missing steps, stops early)",
    "copy": "clear, specific, helpful wording",
    "accuracy": "numbers or facts correct (or wrong, rounded, invented)",
    "trust_safety": "calm, honest, trustworthy; protective information such as FSCS, scam warnings, regulatory wording",
    "scaffolding": "prototype controls, annotations, draft or placeholder text, wireframe or web-form feel",
    "layout_defects": "cropped, clipped, overlapping, broken layout",
    "clutter": "cluttered, busy, repeated content",
}
PROMPT = """A design reviewer compared two bank-app designs and wrote one sentence explaining the choice.
Design %s was judged the better one overall. Reviewer's sentence:
"%s"

Themes: %s

Return only JSON: {"decisive": "<the one theme that mainly decided the choice>", "for_winner": [themes the sentence praises in the winning design], "against_loser": [themes the sentence criticises in the losing design]}. Use only theme names from the list."""
LOCK = threading.Lock()


def ask(sentence, winner):
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    body = {"model": "anthropic/claude-sonnet-5.5", "temperature": 0, "messages": [{"role": "user", "content":
            PROMPT % (winner, sentence, "; ".join(f"{k} = {v}" for k, v in THEMES.items()))}]}
    for _ in range(4):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=120, headers={"Authorization": f"Bearer {key}"})
            j = json.loads(re.search(r"\{.*\}", r.json()["choices"][0]["message"]["content"], re.S).group(0))
            if j.get("decisive") in THEMES:
                return {"decisive": j["decisive"], "for_winner": [t for t in j.get("for_winner", []) if t in THEMES], "against_loser": [t for t in j.get("against_loser", []) if t in THEMES]}
        except Exception:
            pass
    return None


def main(stage):
    stage = Path(stage)
    out = stage / "reasons-coded.jsonl"
    done = {(r["src"], r["judge"], r["brief"], r["rep"], r["view"], r["first"]) for r in map(json.loads, out.open())} if out.exists() else set()
    jobs = []
    for f in sorted(stage.glob("pairs-*.jsonl")):
        src = "cropped" if "crop-" in f.name else "original"
        for r in map(json.loads, f.open()):
            k = (src, r["judge"], r["brief"], r["rep"], r["view"], r["first"])
            if "error" not in r and k not in done and r["overall"] in ("1", "2"):
                jobs.append((k, r))

    def one(j):
        k, r = j
        c = ask(r["reason"], r["overall"])
        if c:
            arm = r["first"] if r["overall"] == "1" else ("B" if r["first"] == "A" else "A")
            with LOCK, out.open("a") as fh:
                fh.write(json.dumps({"src": k[0], "judge": k[1], "brief": k[2], "rep": k[3], "view": k[4], "first": k[5], "winner_arm": arm, "reason": r["reason"], **c}) + "\n")
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(one, jobs))
    rows = [json.loads(l) for l in out.open()]
    md = ["# Why the judges chose what they chose", "",
          f"{len(rows)} judge sentences (both judges, both orders, original and cropped screens, both views; votes where the judge "
          "picked a design overall) coded by a model into themes. Counts are approximate and descriptive.", ""]
    for title, flt in (("All votes", lambda r: True), ("Looks view", lambda r: r["view"] == "looks"), ("Whole-design view", lambda r: r["view"] == "whole")):
        sel = [r for r in rows if flt(r)]
        n = Counter(r["winner_arm"] for r in sel)
        md += [f"## {title}", "", f"Plain won {n['A']} votes, factory won {n['B']}. Share of each arm's winning votes whose sentence names the theme "
               "as the deciding one, and as a strength of the winner or a fault of the loser.", "",
               "| Theme | Deciding theme, plain won | Deciding theme, factory won | Praised in the winner, plain won | Praised in the winner, factory won | Faulted in the factory design, plain won | Faulted in the plain design, factory won |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for t in THEMES:
            def sh(arm, fld, dec=False):
                s = [r for r in sel if r["winner_arm"] == arm]
                return f"{sum((r['decisive'] == t) if dec else (t in r[fld]) for r in s) / max(1, len(s)):.0%}"
            md.append(f"| {t} | {sh('A', '', True)} | {sh('B', '', True)} | {sh('A', 'for_winner')} | {sh('B', 'for_winner')} | {sh('A', 'against_loser')} | {sh('B', 'against_loser')} |")
        md.append("")
    (stage / "analysis-reasons.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main(sys.argv[1])
