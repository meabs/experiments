"""Does the storyboard apply the research? One vision-model call per run, blind to the arm.
The judge reads the run's research.md (its findings and its numbered decisions) and looks at the storyboard's frames
(the same pages as the preference judgement, up to 18 frames). For each decision the agent listed it says whether the
decision is visibly applied in the frames shown (true or false, with a one-sentence reason naming the frame). It also
says whether the research names specific current trends or styles with a source (not generalities).
Score: applied decisions / decisions listed (0 if no decisions were listed). A decision that is a statement about
process (for example "I will read more sources") is not countable and is excluded by the judge.

Usage: python3 judge_research.py <stage dir> [--judge MODEL]   -> <stage dir>/research-<model slug>.jsonl (resumable)
"""
import base64, io, json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

LOCK = threading.Lock()
PROMPT = """An AI agent was asked to research current trends and styles in mobile banking app design, then to
develop a storyboard of a banking scenario from that research. Below are its research notes (RESEARCH) and the frames
of its storyboard (images, in journey order, numbered on each page). Judge only what is visible in the images and
written in the notes.

RESEARCH:
<<<
%s
>>>

Tasks:
1. List the numbered decisions the agent says it will take into the design (R1, R2, ...). If it listed none, return an
   empty list. Leave out decisions that are about its own process rather than the design.
2. For each, say whether it is visibly applied in the frames shown: applied true or false, and one sentence of
   evidence naming the frame number.
3. Say whether the research names specific current trends or styles with a source for each (specific: true) or stays
   generic (specific: false).

Return only JSON: {"decisions": [{"id": "R1", "applied": true|false, "evidence": "<one sentence>"}], "specific": true|false}"""


def slug(m):
    return re.sub(r"[^a-z0-9]+", "-", m.lower()).strip("-")


def img(p):
    buf = io.BytesIO()
    Image.open(p).convert("RGB").save(buf, "JPEG", quality=85)
    return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}}


def ask(model, research, pages):
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    content = [{"type": "text", "text": PROMPT % research[:14000]}] + [img(p) for p in pages]
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
            out = json.loads(re.search(r"\{.*\}", j["choices"][0]["message"]["content"], re.S).group(0))
            assert isinstance(out["decisions"], list)
            return out, j.get("usage", {}).get("cost", 0)
        except (ValueError, KeyError, TypeError, AttributeError, AssertionError) as e:
            last = f"parse: {e}"
    return {"error": last}, 0


def main(stage, model):
    stage = Path(stage)
    out = stage / f"research-{slug(model)}.jsonl"
    done = {j["run"] for j in map(json.loads, out.open()) if "error" not in j} if out.exists() else set()
    jobs = []
    for ev in sorted(stage.glob("eval/*/*/*/eval.json")):
        brief, arm, rep = ev.parts[-4:-1]
        run = f"{brief}/{arm}/{rep}"
        rf = stage / arm / "runs" / brief / arm / "codex" / rep / "artefacts" / "research.md"
        pages = sorted(ev.parent.glob("p[0-9].png"))
        if run not in done:
            jobs.append((run, brief, arm, rep, rf.read_text(errors="replace") if rf.exists() else "", pages))

    def one(job):
        run, brief, arm, rep, text, pages = job
        rec = {"run": run, "brief": brief, "arm": arm, "rep": rep, "judge": model}
        if not text.strip() or not pages:
            rec.update(decisions=[], specific=False, cost=0, note="no research.md or no frames")
        else:
            v, cost = ask(model, text, pages)
            rec.update(v, cost=cost)
        with LOCK, out.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")

    with ThreadPoolExecutor(int(os.environ.get("DF_JUDGE_WORKERS", "4"))) as ex:
        list(ex.map(one, jobs))
    print(len(jobs), "runs judged by", model, "->", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    model = "google/gemini-4-argon"
    if "--judge" in args:
        i = args.index("--judge")
        model = args[i + 1]
        del args[i:i + 2]
    main(args[0], model)
