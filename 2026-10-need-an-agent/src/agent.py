"""Architecture 4, agent: the model works in a loop with the shop's tools and decides its own steps. Same model,
policy and tools as the others. It stops when it answers without calling a tool (that answer is the reply), or after
MAX_STEPS model calls, in which case the code escalates and sends a holding reply.
"""
import json

from shop import TODAY, tool_schemas

POLICY = open(__file__.replace("agent.py", "policy.md")).read()
MAX_STEPS = 15

SYSTEM = f"""You handle customer emails for Hartley & Finch, an online homeware shop. Today is {TODAY}.
Use the tools to look things up and to act. Follow this policy exactly:

{POLICY}

When you have finished, answer with the email to send the customer (no tool call). It must state the outcome, amounts
in £ and relevant dates."""

HOLDING = ("Hello,\n\nThanks for your message. We've passed it to a colleague, who will be in touch within 1 working "
           "day.\n\nHartley & Finch")


def run(email, shop, llm):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"From: {email['sender']}\nSubject: {email['subject']}\n\n{email['body']}"}]
    tools = tool_schemas()
    for _ in range(MAX_STEPS):
        m = llm.chat(msgs, tools=tools)
        calls = m.get("tool_calls") or []
        if not calls:
            return m.get("content") or ""
        msgs.append({"role": "assistant", "content": m.get("content") or "", "tool_calls": calls})
        for c in calls:
            try:
                args = json.loads(c["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = None
            out = shop.call(c["function"]["name"], args) if isinstance(args, dict) else {"error": "400 arguments are not valid JSON"}
            msgs.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps(out)})
    shop.call("escalate", {"team": "support", "reason": "agent step limit reached"})
    return HOLDING
