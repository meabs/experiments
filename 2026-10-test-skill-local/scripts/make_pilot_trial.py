"""Writes trial-pilot.local.toml: the 3-4 hour pilot (README amendment log, 2026-10-23): arms A (`none`) and G (`stop`),
10 tasks drawn with random.Random(1).sample(sorted(task ids), 10), 1 run each, 10-minute limit (no hosted run in TSK's
A, B, E or F took over 600 s, so the limit changes no hosted result). Built from ../2026-10-test-skill/trial.local.toml
so the agent, setup and grader are the same. Usage: python3 -I make_pilot_trial.py   (after setup/localize-linux.sh)"""
import os, random, re, tomllib
HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE)
s = open(os.path.join(N, "..", "2026-10-test-skill", "trial.local.toml")).read()
ids = sorted(q["id"] for q in tomllib.loads(s)["questions"])
pick = set(random.Random(1).sample(ids, 10))
prefix = open(os.path.join(N, "arms", "stop.md")).read().rstrip("\n")
arms = list(re.finditer(r'^\[\[arms\]\]\n(.*?)(?=^\[\[)', s, re.S | re.M))
none = next(m for m in arms if re.search(r'^name = "none"$', m.group(1), re.M)).group(0)
stop = none.replace('name = "none"', 'name = "stop"\nprompt_prefix = """' + prefix + '"""', 1)
s = s[:arms[0].start()] + none + stop + s[arms[-1].end():]
qs = list(re.finditer(r'^\[\[questions\]\]\n(.*?)(?=^\[\[|\Z)', s, re.S | re.M))
keep = [m.group(0) for m in qs if re.search(r'^id = "([^"]+)"', m.group(1), re.M).group(1) in pick]
s = s[:qs[0].start()] + "".join(keep)
s = re.sub(r'^reps = \d+', 'reps = 1', s, flags=re.M)
s = re.sub(r'^timeout = \d+', 'timeout = 600', s, flags=re.M)
s = "# PILOT (A + G, 10 drawn tasks, 1 rep, 600 s), by 2026-10-test-skill-local/scripts/make_pilot_trial.py.\n" + s
t = tomllib.loads(s)
assert [a["name"] for a in t["arms"]] == ["none", "stop"] and sorted(q["id"] for q in t["questions"]) == sorted(pick)
assert t["defaults"]["reps"] == 1 and t["defaults"]["timeout"] == 600 and "qwen3.8:27b" in t["agents"][0]["command"]
open(os.path.join(N, "trial-pilot.local.toml"), "w").write(s)
print("trial-pilot.local.toml: tasks", sorted(pick), "| arms none, stop | reps 1 | timeout 600")
