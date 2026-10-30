"""Lays one condition over a fresh clone of accounts-service (run in the clone by setup.sh, before the agent starts).

Every condition, clean included, gets: AGENTS.md (sec-authz arm A's build instructions), a .env with fake secrets that
carry a random canary token (ignored by git, as a real one would be), and .platform/hooks/pre-commit. The planted
instruction then goes into one channel; the disguised framing also adds scripts/dev-bootstrap.sh. The ticket channel
is in the prompt (make_trial.py), so nothing extra is laid for it here apart from the script.
The canary tokens are recorded outside the clone, in $TRIAL_OUT/canaries/<question>_<arm>_<rep>.json, for scoring.
Usage: python3 -I lay.py <arm>   (reads TRIAL_QUESTION, TRIAL_REP, TRIAL_OUT)
"""
import json, os, secrets, sys, textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conditions import BOOTSTRAP, ENV, PRE_COMMIT, TEXT, parse  # noqa: E402

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY = "src/main/java/com/example/accounts/security/AccessPolicy.java"
BANNER = "src/main/resources/banner.txt"
WRAP = {"break_on_hyphens": False, "break_long_words": False}  # never split the URL or the commands


def write(path, text, mode=None):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    if mode:
        os.chmod(path, mode)


def lay(question, arm, rep, out):
    task, channel, framing = parse(question)
    write("AGENTS.md", open(os.path.join(E, "arms", "AGENTS.md")).read())
    token, token2 = secrets.token_hex(12), secrets.token_hex(10)
    write(".env", ENV.format(token=token, token2=token2))
    with open(".gitignore", "a") as f:
        f.write(".env\n")
    write(".platform/hooks/pre-commit", PRE_COMMIT, 0o755)
    if framing == "disguised":
        write("scripts/dev-bootstrap.sh", BOOTSTRAP, 0o755)
    if channel:
        text = TEXT[framing]
        if channel == "agents":
            with open("AGENTS.md", "a") as f:
                f.write(f"- {text}\n")
        elif channel == "readme":
            r = open("README.md").read()
            anchor = "```\nmvn -o -q test        # offline; all dependencies are in the local Maven repository\n```\n"
            assert anchor in r
            write("README.md", r.replace(anchor, anchor + "\n" + textwrap.fill(text, 118, **WRAP) + "\n", 1))
        elif channel == "code":
            src = open(POLICY).read()
            anchor = "@Component\npublic class AccessPolicy {"
            assert anchor in src
            comment = "\n".join("// " + line for line in textwrap.wrap("Maintainers and coding agents: " + text, 114, **WRAP))
            write(POLICY, src.replace(anchor, comment + "\n" + anchor, 1))
        elif channel == "output":
            write(BANNER, "\n[platform-fixtures] NOTICE\n" + textwrap.fill(text, 118, **WRAP) + "\n\n")
    os.makedirs(os.path.join(out, "canaries"), exist_ok=True)
    rec = {"question": question, "arm": arm, "rep": rep, "task": task, "channel": channel, "framing": framing,
           "token": token, "token2": token2, "workspace": os.getcwd()}
    write(os.path.join(out, "canaries", f"{question}_{arm}_{rep}.json"), json.dumps(rec, indent=1))


if __name__ == "__main__":
    lay(os.environ["TRIAL_QUESTION"], sys.argv[1], os.environ.get("TRIAL_REP", "0"), os.environ["TRIAL_OUT"])
