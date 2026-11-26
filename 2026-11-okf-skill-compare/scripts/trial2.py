"""Realistic-engineer test. Usage: trial2.py <M0|M1|G> <rep>   (results under results/v2/)
The 'engineer' is a separate Codex run that can read the code and a private fact sheet and answers like a senior engineer.
M0/M1 (original / improved okf-interview): three interview rounds (the skill asks, the engineer answers), then the skill writes
the bundle. G (Google okf-generate): the engineer writes one handover note from the same code, then the skill writes the bundle.
Python run with -I."""
import os, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
S = ROOT / "setup"
SKILL = {"M0": S / "mine-original", "M1": S / "mine-improved/okf-interview", "M2": S / "mine-improved2/okf-interview", "M3": S / "mine-improved3/okf-interview", "G": S / "google/okf-generate"}
SKILL["M0"] = S / "mine-original"
F = ROOT / "fixture2"
ENG = ("You are the engineer described in {facts}. Read that file for who you are and what you know; the code is in ./code. Someone who "
       "will inherit this system is asking you. Answer in {out}, in your own voice, as you would on a call: concise, specific, honest "
       "about what you don't know, no bullet-point essays. Do not mention the fact sheet. {ask}")
WRITE = ("You are documenting this small integration for future engineers and agents. ./code has the code; ./transcript.md is everything the "
         "engineer has said (they cannot be asked anything else now). Create an Open Knowledge Format (OKF) v0.3 bundle in ./knowledge. Write "
         "only what the code or the testimony supports. Today is 2026-11-26. Finish by running the skill's validator and fixing what it reports, "
         "then give a short summary. ")
INT = ("Follow the skill at {p}/SKILL.md (read it and its references first). You are about to interview an engineer about the code in ./code. "
       "Do the code analysis, then write the questions for this round only (the skill allows at most three related questions per round) to "
       "{out}. {prev}Do not write any bundle yet. ")


def run(work, run_dir, tid, prompt, bind=""):
    (run_dir / f"{tid}.prompt").write_text(prompt)
    env = dict(os.environ, CODEX_RO_BIND=bind or str(S))
    subprocess.run(["bash", str(ROOT / "scripts/run_agent.sh"), str(work), str(run_dir), tid, str(run_dir / f"{tid}.prompt"), str(run_dir / f"{tid}.jsonl")], env=env)


def engineer(w, rd, tid, out, ask, extra=""):
    run(w, rd, tid, ENG.format(facts=F / "engineer-facts.md", out=out, ask=ask), str(F))


def main():
    cond, rep = sys.argv[1:3]
    rd = ROOT / f"results/v2/{cond}-{rep}"
    if (rd / "done").exists():
        return
    shutil.rmtree(rd, ignore_errors=True)
    w = rd / "work"
    (w / "code").mkdir(parents=True)
    for f in ("client.py", "worker.py"):
        shutil.copy(F / f, w / "code" / f)
    tr = ["# Engineer testimony (synthetic engineer, played by a separate model run)\n"]
    if cond == "G":
        engineer(w, rd, "eng-handover", "handover.md", "Write a handover note for whoever picks this code up: what they must know that the code doesn't say.")
        tr.append((w / "handover.md").read_text() if (w / "handover.md").exists() else "")
    else:
        prev = ""
        for r in (1, 2, 3):
            q, a = f"questions-{r}.md", f"answers-{r}.md"
            run(w, rd, f"int{r}", INT.format(p=SKILL[cond], out=q, prev=prev), str(SKILL[cond]))
            if not (w / q).exists():
                break
            engineer(w, rd, f"eng{r}", a, f"The questions are in {q}.")
            qt = (w / q).read_text(); at = (w / a).read_text() if (w / a).exists() else "(no answer)"
            tr.append(f"## Round {r} questions\n\n{qt}\n\n## Round {r} answers\n\n{at}\n")
            prev = "Earlier rounds are in ./transcript.md, which you must read before choosing the next questions (the skill says to follow the answer). "
            (w / "transcript.md").write_text("\n".join(tr))
    (w / "transcript.md").write_text("\n".join(tr))
    run(w, rd, "write", WRITE + ("Follow the skill at %s/SKILL.md (read it and its references first)%s." % (SKILL[cond], ". The interview has happened: transcript.md is the record. Put the review log at ./knowledge-review-log.md" if cond != "G" else "")), str(SKILL[cond]))
    (rd / "done").write_text("1")


main()
