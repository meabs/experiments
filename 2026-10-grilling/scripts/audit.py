"""Audits the developer's replies (mine) against the brief: did any reply give a left-out requirement that the agent's
message didn't touch?

For every developer reply after the first turn, a judge model (openai/gpt-6-luna through OpenRouter, JSON mode) is
given the task's brief, the agent's message and the reply, and says for each left-out requirement whether the reply
states it, whether the agent's message asked about it or touched its topic, and whether the message asked an open
question ("anything else?"). A leak is a requirement the reply states that the message didn't touch, unless it is the
top-of-mind requirement given in answer to an open question.

  python3 -I audit.py <run> [<run> ...]      writes <run>/audit.json and prints the leaks
"""
import json, os, re, sys

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(E), "2026-10-need-an-agent", "src"))
from llm import LLM, parse_json  # noqa: E402

W = os.environ.get("GRILL_WORK", os.path.expanduser("~/code/benchmark/grilling-work"))
JUDGE = "openai/gpt-6-luna"

PROMPT = """You are auditing a simulated developer. The developer has a private brief listing requirements that a ticket
left out. The developer must only give a requirement when the agent's message asks about it or touches its topic (for
example asks who may do the action, what happens to related records, or proposes an answer about it). In answer to an
open question ("anything else I should know?") the developer may give the requirement marked top of mind.

BRIEF (stage 1 part only):
{brief}

AGENT'S MESSAGE:
{agent}

DEVELOPER'S REPLY:
{reply}

For each requirement id in the brief ({ids}), answer with JSON:
{{"items": {{"<id>": {{"stated_in_reply": true|false, "touched_by_message": true|false}}, ...}},
  "open_question_in_message": true|false,
  "other_information_beyond_brief": "<anything in the reply that is neither in the brief nor a plain yes/no/your call, or empty>"}}
"touched_by_message" means the message asks about, or proposes an answer on, the specific question that requirement
settles (for example who may do something, or what must be recorded), not merely the same field or endpoint. A
question about a value's format or range does not touch a rule about who may set it.
"open_question_in_message" is true only if the message explicitly invites the developer to add anything not yet
covered ("anything else I should know?", "any other requirements?"); a specific question with several options is not
an open question.
"stated_in_reply" means the reply tells the agent the substance of that requirement (not just "yes" to a proposal
that happens to match it; a plain "yes" accepting the agent's own proposal is not stating it)."""


def brief_stage1(task):
    text = open(os.path.join(E, "tasks", task, "developer.md")).read()
    return text.split("## Follow-up ticket")[0]


def audit(run):
    d = os.path.join(W, run)
    m = json.load(open(os.path.join(d, "meta.json")))
    brief = brief_stage1(m["task"])
    ids = re.findall(r"\*\*(r[a-d]) \(", brief)
    top = re.findall(r"\*\*(r[a-d]) \([^)]*top of mind", brief)
    llm, rows = LLM(JUDGE), []
    for n in range(2, m["turns"] + 1):
        agent = open(os.path.join(d, "turns", f"{n - 1:02d}.agent.md")).read()
        reply = open(os.path.join(d, "turns", f"{n:02d}.dev.md")).read()
        if not ids:
            rows.append({"turn": n, "leaks": [], "items": {}})
            continue
        msg = llm.chat([{"role": "user", "content": PROMPT.format(brief=brief, agent=agent, reply=reply,
                                                                  ids=", ".join(ids))}], json_mode=True)
        j = parse_json(msg.get("content")) or {}
        items = j.get("items", {})
        leaks = [i for i in ids if items.get(i, {}).get("stated_in_reply") and not items.get(i, {}).get("touched_by_message")
                 and not (i in top and j.get("open_question_in_message"))]
        excused = [i for i in ids if items.get(i, {}).get("stated_in_reply")
                   and not items.get(i, {}).get("touched_by_message") and i not in leaks]
        rows.append({"turn": n, "items": items, "open_question": j.get("open_question_in_message"), "top_of_mind_given": excused,
                     "other": j.get("other_information_beyond_brief", ""), "leaks": leaks})
    out = {"run": run, "judge": JUDGE, "turns": rows, "leaks": sum(len(r["leaks"]) for r in rows), "usage": llm.usage()}
    json.dump(out, open(os.path.join(d, "audit.json"), "w"), indent=1)
    return out


if __name__ == "__main__":
    for r in sys.argv[1:]:
        o = audit(r)
        print(r, "leaks", o["leaks"], [(t["turn"], t["leaks"], t.get("other")) for t in o["turns"] if t["leaks"] or t.get("other")])
