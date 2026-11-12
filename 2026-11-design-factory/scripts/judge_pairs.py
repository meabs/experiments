"""Blind side-by-side judging of the designs by two vision models from providers other than the agent's.

Pairs: within each brief, plain run i is paired with factory run i (fixed before any run). For each pair, each judge
answers four times: two views x two orders (which design is shown first is swapped, to cancel position bias).
  view "looks": the first six screens of each design (pages p1, p2) - visual design only
  view "whole": every screen, up to 18 (pages p1..p6)           - the design as a whole
The judge sees only the brief and the images, labelled Design 1 and Design 2. It never sees file names, screen ids,
the arm, or any process files. Output per call: for each criterion "1", "2" or "tie", plus one sentence of reason.

Usage: python3 judge_pairs.py <stage dir> [--judge MODEL]   -> <stage dir>/pairs-<model slug>.jsonl (resumable)
"""
import base64, io, json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

E = Path(__file__).resolve().parent.parent
LOCK = threading.Lock()
CRITERIA = {
    "hierarchy": "visual hierarchy: on each screen it is obvious what matters most and what to do next",
    "polish": "visual polish: consistent components, spacing, alignment and typography; looks finished",
    "identity": "a deliberate, distinctive look that suits a bank, as opposed to generic defaults",
    "content": "the words: clear, specific, helpful headings, labels, buttons and messages",
    "trust": "would a customer trust this with their money: calm, exact, honest, nothing confusing or alarming without reason",
    "journey": "the journey: the right steps in a sensible order, and the situations a real customer could hit are designed, not only the ideal path",
    "overall": "overall: which design should the bank's design lead take forward",
}
PROMPT = """You are an experienced product design lead at a UK bank, reviewing two designs made independently for the
same brief. Judge only what you can see in the screenshots. The designs may have different numbers of screens; do not
reward a design merely for having more screens, and do not penalise it for having more.

THE BRIEF:
%s

%s

For each criterion say which design is better: "1", "2", or "tie" if you genuinely cannot separate them.
Criteria:
%s

Return only JSON: {%s, "reason": "<one sentence on what decided the overall choice>"}"""


def slug(model):
    return re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")


def img(path):
    im = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}}


def ask(model, brief, first, second, view):
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    crit = {k: v for k, v in CRITERIA.items() if not (view == "looks" and k == "journey")}
    note = ("You are shown the first six screens of each design." if view == "looks"
            else "You are shown every screen of each design, in journey order.")
    text = PROMPT % (brief, note, "\n".join(f"- {k}: {v}" for k, v in crit.items()),
                     ", ".join(f'"{k}": "1"|"2"|"tie"' for k in crit))
    content = [{"type": "text", "text": text}, {"type": "text", "text": "DESIGN 1:"}] + [img(p) for p in first] + \
              [{"type": "text", "text": "DESIGN 2:"}] + [img(p) for p in second]
    body = {"model": model, "temperature": 0, "usage": {"include": True}, "messages": [{"role": "user", "content": content}]}
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
            t = j["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", t, re.S)
            out = json.loads(m.group(0))
            if all(str(out.get(k)) in ("1", "2", "tie") for k in crit):
                return {k: str(out[k]) for k in crit} | {"reason": str(out.get("reason", ""))[:400]}, j.get("usage", {}).get("cost", 0)
            last = f"bad verdicts {out}"
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            last = f"parse: {e}"
    return {"error": last}, 0


def main(stage, model, crop=False):
    stage = Path(stage)
    ev = "eval-crop" if crop else "eval"  # --crop: exploratory re-score on screens cropped to their interior (crop.py)
    out = stage / f"pairs-{'crop-' if crop else ''}{slug(model)}.jsonl"
    done = {(j["brief"], j["rep"], j["view"], j["first"]) for j in map(json.loads, out.open()) if "error" not in j} if out.exists() else set()
    jobs = []
    for a in sorted(stage.glob(ev + "/*/A/*")):
        brief, rep = a.parts[-3], a.parts[-1]
        b = stage / ev / brief / "B" / rep
        pa, pb = sorted(a.glob("p[0-9].png")), sorted(b.glob("p[0-9].png"))
        if not pa or not pb:
            continue  # a run with no screens loses the pair by rule (analyse.py); nothing to judge
        text = (E / "briefs" / brief / "prompt.md").read_text().strip()
        for view in ("looks", "whole"):
            n = 2 if view == "looks" else 6
            for first in ("A", "B"):
                if (brief, rep, view, first) not in done:
                    jobs.append((brief, rep, view, first, text, (pa[:n], pb[:n]) if first == "A" else (pb[:n], pa[:n])))

    def one(job):
        brief, rep, view, first, text, (p1, p2) = job
        v, cost = ask(model, text, p1, p2, view)
        with LOCK, out.open("a") as fh:
            fh.write(json.dumps({"brief": brief, "rep": rep, "view": view, "first": first, "judge": model, **v, "cost": cost}) + "\n")

    with ThreadPoolExecutor(int(os.environ.get("DF_JUDGE_WORKERS", "4"))) as ex:
        list(ex.map(one, jobs))
    print(len(jobs), "calls by", model, "->", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    model = "google/gemini-4-argon"
    if "--judge" in args:
        i = args.index("--judge")
        model = args[i + 1]
        del args[i:i + 2]
    crop = "--crop" in args
    if crop:
        args.remove("--crop")
    main(args[0], model, crop)
