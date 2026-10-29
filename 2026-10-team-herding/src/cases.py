"""Builds cases.json from 2026-10-evidence-manipulation (README, "Cases"). No language model is used.

Cases: the 21 observable scenarios with one falsified fact (variant "falsified"), plus 9 of the same scenarios with clean
evidence, chosen with random.Random(2026).sample. Each case keeps only what the agent may see (alert and evidence);
the source files' SHA-256 hashes are recorded so the scorer can check it reads the same ground truth.
Usage: python3 -I src/cases.py
"""
import hashlib, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
EM = os.path.join(os.path.dirname(ROOT), "2026-10-evidence-manipulation")
FILES = ("scenarios/scenarios.json", "scenarios/ground_truth.json", "manipulations/variants.json")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    S = {s["id"]: s for s in json.load(open(os.path.join(EM, "scenarios", "scenarios.json")))}
    H = json.load(open(os.path.join(EM, "scenarios", "ground_truth.json")))
    V = json.load(open(os.path.join(EM, "manipulations", "variants.json")))
    obs = sorted(k for k, h in H.items() if h["kind"] == "observable")
    clean = sorted(random.Random(2026).sample(obs, 9))
    cases = [dict(case=f"{i}-falsified", scenario=i, variant="falsified", alert=S[i]["alert"], evidence=V[i]["falsified"]) for i in obs]
    cases += [dict(case=f"{i}-clean", scenario=i, variant="clean", alert=S[i]["alert"], evidence=V[i]["clean"]) for i in clean]
    json.dump(dict(source={f: sha(os.path.join(EM, f)) for f in FILES}, cases=cases),
              open(os.path.join(ROOT, "cases.json"), "w"), indent=1)
    print(len(cases), "cases:", len(obs), "falsified,", len(clean), "clean", clean)


if __name__ == "__main__":
    main()
