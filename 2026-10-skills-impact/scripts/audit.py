"""Retrospective audits of the stage-1 data. Writes results/retro/audit.json and prints a summary.

1. Regrade every run from its Maven log alone (an independent parser) and compare with verify-summary.json.
   It also checks that each hidden suite ran its full number of tests with none skipped.
2. Isolation: search the control and placebo arms' event logs for any trace of the packs' skills.

Usage: python3 -I audit.py <runs dir> <hidden dir> <out json>
"""
import glob, gzip, json, os, re, sys

SUITE = re.compile(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+).*? - in ([\w.$]+)")
ANSI = re.compile(r"\x1b\[[0-9;]*m")
PACK_TRACES = re.compile(r"using-superpowers|test-driven-development|systematic-debugging|verification-before-completion|"
                         r"diagnosing-bugs|poteto-mode|\.agents/skills|\.cursor/skills|\.claude/skills|SKILL\.md")


def expected_hidden(hidden_dir):
    return {q: sum(open(f).read().count("@Test") for f in glob.glob(os.path.join(hidden_dir, q, "*.java")))
            for q in os.listdir(hidden_dir) if os.path.isdir(os.path.join(hidden_dir, q))}


def regrade_log(text, expected):
    """Pass from the Maven log alone: every module built, hidden suites ran `expected` tests, none skipped,
    and no suite anywhere had a failure or error."""
    text = ANSI.sub("", text)
    hidden_run = hidden_skipped = 0
    bad = []
    for run, f, e, s, suite in SUITE.findall(text):
        if ".hidden." in suite:
            hidden_run += int(run)
            hidden_skipped += int(s)
        if int(f) + int(e):
            bad.append(suite)
    built = "BUILD SUCCESS" in text and "COMPILATION ERROR" not in text
    ok = built and hidden_run == expected and hidden_skipped == 0 and not bad
    return {"built": built, "hidden_run": hidden_run, "hidden_skipped": hidden_skipped, "bad_suites": sorted(set(bad)),
            "pass": ok}


def main():
    runs, hidden, out = sys.argv[1:4]
    exp = expected_hidden(hidden)
    regrade, leaks = {}, {}
    for f in sorted(glob.glob(os.path.join(runs, "*/*/*/*/verify-summary.json"))):
        rd = os.path.dirname(f)
        key = os.path.relpath(rd, runs)
        q, arm = key.split("/")[:2]
        log = gzip.open(os.path.join(rd, "verify-mvn.log.gz"), "rt", errors="replace").read()
        r = regrade_log(log, exp[q])
        r["recorded_pass"] = json.load(open(f))["pass"]
        r["agree"] = r["pass"] == r["recorded_pass"]
        regrade[key] = r
        if arm in ("none", "placebo"):
            raw = gzip.open(os.path.join(rd, "raw.out.gz"), "rt", errors="replace").read()
            hits = sorted(set(PACK_TRACES.findall(raw)) - ({"SKILL.md", ".agents/skills"} if arm == "placebo" else set()))
            if arm == "placebo":
                hits = [h for h in hits if "careful-engineering" not in h]
            leaks[key] = hits
    res = {"expected_hidden": exp, "regrade": regrade, "isolation": leaks}
    json.dump(res, open(out, "w"), indent=1)
    dis = [k for k, v in regrade.items() if not v["agree"]]
    short = [k for k, v in regrade.items() if v["hidden_run"] != exp[k.split("/")[0]] or v["hidden_skipped"]]
    print(f"regrade agrees on {len(regrade) - len(dis)}/{len(regrade)} runs; disagreements: {dis}")
    print(f"runs with a hidden suite short or skipped: {short}")
    print(f"control/placebo runs with any pack trace: {[k for k, v in leaks.items() if v]}")


if __name__ == "__main__":
    main()
