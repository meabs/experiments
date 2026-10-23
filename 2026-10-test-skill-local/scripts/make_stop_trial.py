"""Writes trial-stop.local.toml (arm G, local only, exploratory) from ../2026-10-test-skill/trial.local.toml, so it shares
the localized agent, tasks, setup and grader exactly. Arm G is arm A (`none`) with arms/stop.md before the task.
Usage: python3 -I make_stop_trial.py   (after setup/localize-linux.sh)"""
import os, re, tomllib
HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE)
src = os.path.join(N, "..", "2026-10-test-skill", "trial.local.toml")
s = open(src).read()
prefix = open(os.path.join(N, "arms", "stop.md")).read().rstrip("\n")
arms = list(re.finditer(r'^\[\[arms\]\]\n(.*?)(?=^\[\[)', s, re.S | re.M))
none = next(m for m in arms if re.search(r'^name = "none"$', m.group(1), re.M))
stop = none.group(0).replace('name = "none"', 'name = "stop"\nprompt_prefix = """' + prefix + '"""', 1)
s = s[:arms[0].start()] + stop + s[arms[-1].end():]
s = re.sub(r'^baseline = "none"', 'baseline = "stop"  # only arm in this file; affects the rig report only', s, flags=re.M)
s = s.replace("# LOCALIZED by", "# ARM G (stop), from 2026-10-test-skill/trial.local.toml by 2026-10-test-skill-local/scripts/make_stop_trial.py.\n# LOCALIZED by", 1)
t = tomllib.loads(s)
assert [a["name"] for a in t["arms"]] == ["stop"] and len(t["questions"]) == 20
open(os.path.join(N, "trial-stop.local.toml"), "w").write(s)
print("trial-stop.local.toml:", len(t["questions"]), "tasks, arm", t["arms"][0]["name"], "timeout", t["defaults"]["timeout"])
