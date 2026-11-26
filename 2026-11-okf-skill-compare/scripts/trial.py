"""OKF skill comparison. Usage: trial.py write <M|G> <rep> | read <M|G> <rep> <P|K>   (results under results/main/)
write: agent builds a bundle from fixture/client.py + fixture/notes.md using one skill. read: a second agent answers questions.md
from that bundle, plainly (P) or with Google's okf-consume (K). Python run with -I."""
import json, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SETUP = ROOT / "setup"
SK = {"M": SETUP / "mine-original", "G": SETUP / "google/okf-generate"}
CONSUME = SETUP / "google/okf-consume"
WRITE = ("You are documenting a small integration for future engineers and agents. The current folder has client.py (the code) and "
         "notes.md (everything the engineer said; they cannot be asked anything else, and this is a single turn). Create an Open "
         "Knowledge Format (OKF) v0.3 bundle in ./knowledge. Write only what the code or the notes support. Today is 2026-11-26. "
         "Finish by running the skill's validator and fixing what it reports, then give a short summary. ")
SPEC = {"M": "Follow the skill at {p}/SKILL.md (read it and its references first). The interview has already happened: notes.md is the "
              "interview record. Put the engineer review log at ./knowledge-review-log.md.",
        "G": "Follow the skill at {p}/SKILL.md (read it and its references first)."}
READ = ("The folder ./knowledge is an OKF bundle about a small integration. Answer the questions in questions.md from the bundle only. "
        "Write answers.json: an object keyed Q1..Q9, each value {\"covered_by_bundle\": \"yes\" or \"no\", \"answer\": \"...\", "
        "\"trust\": \"the trust tier and status of the concept(s) you used, or empty\"}. If the bundle does not say, covered_by_bundle "
        "is \"no\" and the answer says what is missing. Do not use general knowledge as an answer. ")
READ_K = "Use the skill at {p}/SKILL.md (read it and its references first). "


def go(work, run, tid, prompt, extra_bind):
    (run / "prompt.txt").write_text(prompt)
    import os
    env = dict(os.environ, CODEX_RO_BIND=extra_bind)
    subprocess.run(["bash", str(ROOT / "scripts/run_agent.sh"), str(work), str(run), tid, str(run / "prompt.txt"), str(run / "session.jsonl")], env=env)


def main():
    mode, cond, rep = sys.argv[1:4]
    run = ROOT / f"results/main/{mode}-{cond}-{rep}" if mode == "write" else ROOT / f"results/main/read-{cond}-{rep}-{sys.argv[4]}"
    if (run / "done").exists():
        return
    shutil.rmtree(run, ignore_errors=True)
    work = run / "work"
    work.mkdir(parents=True)
    if mode == "write":
        for f in ("client.py", "notes.md"):
            shutil.copy(ROOT / "fixture" / f, work / f)
        go(work, run, f"w{cond}{rep}", WRITE + SPEC[cond].format(p=SK[cond]), str(SK[cond]))
    else:
        rd = sys.argv[4]
        src = ROOT / f"results/main/write-{cond}-{rep}/work/knowledge"
        if not src.exists():
            sys.exit("no bundle")
        shutil.copytree(src, work / "knowledge")
        shutil.copy(ROOT / "fixture/questions.md", work / "questions.md")
        p = READ + (READ_K.format(p=CONSUME) if rd == "K" else "")
        go(work, run, f"r{cond}{rep}{rd}", p, str(CONSUME) if rd == "K" else str(SETUP))
    (run / "done").write_text("1")


main()
