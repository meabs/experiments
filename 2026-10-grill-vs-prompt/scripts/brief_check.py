"""Brief check: a fresh reader (a judge model through OpenRouter, not the author) reads each new ticket with its brief,
its hidden tests and the parts of the repository it touches, and reports whether each left-out requirement is fair.

  python3 -I brief_check.py M1 N1 N2      writes checks/brief-check.md
"""
import os, sys

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(os.path.dirname(E), "2026-10-sec-authz", "app")
sys.path.insert(0, os.path.join(os.path.dirname(E), "2026-10-need-an-agent", "src"))
from llm import LLM  # noqa: E402

READER = "openai/gpt-6-luna"
J = "src/main/java/com/example/accounts/"
REPO = ["README.md", J + "account/Account.java", J + "account/AccountController.java", J + "security/AccessPolicy.java",
        J + "closure/ClosureRequest.java", J + "account/Transaction.java"]
STARTER = [J + "closure/ClosureController.java", "src/main/resources/data.sql"]

PROMPT = """You are reviewing a test task for an experiment, before it is run. A coding agent gets the TICKET and works on
the REPOSITORY. A simulated developer answers the agent's questions from a private BRIEF. Some requirements are left out
of the ticket on purpose. Each is labelled "in the repo" (a careful agent can find it in the code or README) or "in my
head" (it exists nowhere in the repository; only asking the developer gets it). Some briefs nest rules: a "child" rule
only comes up once the agent knows the "parent" rule. HIDDEN TESTS check each requirement (test names start with
ticket_ or r<letter>_).

Judge each left-out requirement, plainly and briefly:
1. Reasonable? Is it something a reasonable colleague would expect to be asked about, or to know, for a ticket like
   this, rather than a trick?
2. Labelled right? Is an "in my head" rule really absent from the ticket and the repository, and is nothing in them
   pointing towards it or against it? Is an "in the repo" rule really findable?
3. Fairly tested? Do the hidden tests check the rule as the brief states it, without demanding details the brief
   leaves as "your call" (wording, exact codes the brief doesn't fix)?
4. For nested briefs: is the parent rule something an agent could plausibly ask about up front, and are the children
   only reachable after it?
Then list anything else that would make the task unfair or broken (for example a ticket test that a correct
implementation could fail). End with a one-line verdict per requirement: OK, or CHANGE: <what>.

TICKET:
{ticket}

BRIEF:
{brief}

HIDDEN TESTS:
{tests}

REPOSITORY (selected files):
{repo}
"""


def read(p):
    return open(p).read()


def main(tasks):
    repo = "\n\n".join(f"--- {p}\n{read(os.path.join(APP, p))}" for p in REPO)
    repo += "\n\n" + "\n\n".join(f"--- {p} (as the agent sees it)\n{read(os.path.join(E, 'starter', p))}" for p in STARTER)
    llm = LLM(READER)
    out = ["# Brief check: fresh reader's report (2026-10-31, before any measured run)", "",
           f"The reader was `{READER}` through OpenRouter, with no part in writing the tasks. For each new ticket it was",
           "given the ticket, the brief, the hidden tests and the repository files the ticket touches, and asked whether",
           "each left-out requirement is reasonable, correctly labelled and fairly tested. Its answers are below as it",
           "gave them. What was changed in response is in the README's amendment log.", ""]
    for t in tasks:
        msg = llm.chat([{"role": "user", "content": PROMPT.format(
            ticket=read(os.path.join(E, "tasks", t, "prompt.md")), brief=read(os.path.join(E, "tasks", t, "developer.md")),
            tests=read(os.path.join(E, "hidden", f"{t}HiddenTest.java")), repo=repo)}])
        out += [f"## {t}", "", (msg.get("content") or "(no answer)").strip(), ""]
        print(t, "done", file=sys.stderr)
    open(os.path.join(E, "checks", "brief-check.md"), "w").write("\n".join(out))
    print(llm.usage(), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:] or ["M1", "N1", "N2"])
