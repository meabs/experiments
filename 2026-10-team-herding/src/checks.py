"""Checks on the runs (README, "Procedure"), from the Codex session files and event streams, not from the agents' claims.
- every call has exactly one session file under its agent home (arm E: one file, resumed), whose turn contexts show the
  expected model and medium effort;
- no event stream or session file mentions the ground truth, evidence-manipulation, or this folder;
- every call has a valid assessment and exit code 0.
Usage: python3 -I src/checks.py <out dir> [<out dir> ...]
"""
import glob, json, os, re, sys

BAD = re.compile(r"ground_truth|evidence-manipulation|team-herding|cases\.json")
for d in sys.argv[1:]:
    calls = [json.loads(l) for l in open(os.path.join(d, "calls.jsonl"))]
    homes = sorted(glob.glob(os.path.join(d, "homes", "*")))
    models, efforts, nfiles, leaks = {}, {}, {}, []
    for h in homes:
        files = glob.glob(os.path.join(h, "sessions", "**", "rollout-*.jsonl"), recursive=True)
        nfiles[os.path.basename(h)] = len(files)
        for f in files:
            text = open(f).read()
            for m in re.finditer(r'"type":"turn_context".*', text):
                line = m.group(0)
                models.setdefault(re.search(r'"model":"([^"]*)"', line).group(1), 0)
                models[re.search(r'"model":"([^"]*)"', line).group(1)] += 1
                e = re.search(r'"effort":"([^"]*)"', line)
                efforts[e.group(1) if e else None] = efforts.get(e.group(1) if e else None, 0) + 1
            if BAD.search(text.replace(d, "")):
                leaks.append(f)
    ev_leaks = [f"{c['case']}/{c['rep']}/{c['stage']}/{c['member']}" for c in calls
                if BAD.search(json.dumps(c["events"]).replace(d, ""))]
    print(f"## {os.path.basename(os.path.abspath(d))}\n")
    print(f"- Calls: {len(calls)}; valid assessments: {sum(1 for c in calls if c['final'])}; exit code 0: "
          f"{sum(1 for c in calls if c['returncode'] == 0)}.")
    print(f"- Agent homes: {len(homes)}; session files per home: {sorted(set(nfiles.values()))}.")
    print(f"- Turn contexts by model: {models}; by effort: {efforts}.")
    print(f"- Session files or event streams mentioning the ground truth, evidence-manipulation or this folder: "
          f"{len(leaks) + len(ev_leaks)}.\n")
