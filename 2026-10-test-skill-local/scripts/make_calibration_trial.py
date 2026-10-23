"""Writes trial-calibration.local.toml: hosted gpt-5.6-luna, arm A only, 1 run per task, through the same localized rig,
Codex 0.157.0, bubblewrap isolation and grader as the local runs (README, "Before the runs", step 5).
Only the model and provider differ from trial.local.toml: CODEX_PROFILE=hosted gives Codex a clean home with the login and
an empty config, as in TSK. Usage: python3 -I make_calibration_trial.py   (after setup/localize-linux.sh)"""
import os, re, tomllib
HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE)
s = open(os.path.join(N, "..", "2026-10-test-skill", "trial.local.toml")).read()
arms = list(re.finditer(r'^\[\[arms\]\]\n(.*?)(?=^\[\[)', s, re.S | re.M))
none = next(m for m in arms if re.search(r'^name = "none"$', m.group(1), re.M))
s = s[:arms[0].start()] + none.group(0) + s[arms[-1].end():]
s = re.sub(r'^reps = \d+', 'reps = 1', s, flags=re.M)
s = s.replace('"--model", "qwen3.8:27b"', '"--model", "gpt-5.6-luna"').replace('model = "qwen3.8:27b"', 'model = "gpt-5.6-luna"')
s = s.replace('PATH = "/usr/lib/jvm/java-21-openjdk-amd64/bin:/usr/local/bin:/usr/bin:/bin" }',
              'PATH = "/usr/lib/jvm/java-21-openjdk-amd64/bin:/usr/local/bin:/usr/bin:/bin", CODEX_PROFILE = "hosted" }')
s = "# HOSTED CALIBRATION (gpt-5.6-luna, arm A, 1 rep), by 2026-10-test-skill-local/scripts/make_calibration_trial.py.\n" + s
t = tomllib.loads(s)
a = t["agents"][0]
assert [x["name"] for x in t["arms"]] == ["none"] and t["defaults"]["reps"] == 1 and len(t["questions"]) == 20
assert "gpt-5.6-luna" in a["command"] and "qwen" not in s.split("[[agents]]")[1] and a["env"]["CODEX_PROFILE"] == "hosted"
open(os.path.join(N, "trial-calibration.local.toml"), "w").write(s)
print("trial-calibration.local.toml:", len(t["questions"]), "tasks, arm none, reps 1, timeout", t["defaults"]["timeout"], "args", a["command"][9:-1])
