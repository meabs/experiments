"""Architecture 3, a 3-agent crew with handoffs, in the style of OpenAI's Swarm / Agents SDK:

  front desk  reads the email, looks the customer up, answers general policy questions, and transfers each request
              to a specialist. It can't change anything.
  delivery    deliveries and order changes: tracking, address changes, cancellations, delivered-but-not-received.
  returns     returns, refunds, damaged items, replacements, stock, billing.

Each agent has its own instructions, the policy sections for its job, and only its own tools, plus
transfer_to_<agent>(note) tools. One agent is active at a time; a transfer makes another agent active. The run ends
when the active agent answers without a tool call: that answer is the reply. All agents share one step budget
(MAX_STEPS model calls, as the single agent); at the limit the code escalates and sends a holding reply.

Two ways of handing over (the variable between the two crew arms):
  shared  the new agent sees the whole conversation so far (the email, every tool call and result), with its own
          instructions in place of the previous agent's (Swarm's default);
  note    the new agent sees only the email and the transferring agent's note (a CrewAI-style task hand-off).
"""
import json, re

import base
from shop import TODAY, tool_schemas

MAX_STEPS = 20


def sections(*names):
    """The policy's '## ' sections with these headings, in the policy's order."""
    parts = re.split(r"(?m)^## ", base.POLICY)
    keep = [p for p in parts[1:] if p.split("\n", 1)[0].strip() in names]
    return "\n".join("## " + p.strip() + "\n" for p in keep)


LOST = ("- **Lost in transit:** if tracking has shown no movement for more than 7 days, the parcel is treated as lost. "
        "Send a replacement (if in stock) or refund it, whichever the customer prefers; if they don't say, send a "
        "replacement.")

AGENTS = {
    "front_desk": {
        "role": "the front desk. You read each email first, look up the customer and their orders, answer general "
                "questions about the policy yourself, and transfer each request about an order to the right "
                "specialist: delivery (tracking, missing parcels, address changes, cancellations) or returns "
                "(returns, refunds, damaged items, replacements, billing). You can't change orders or issue refunds.",
        "policy": base.POLICY.split("\n", 1)[1],
        "tools": ["find_customer", "get_order"],
        "to": ["delivery", "returns"]},
    "delivery": {
        "role": "the delivery specialist. You handle tracking, missing or stuck parcels, address changes and "
                "cancellations. Transfer anything about returns, refunds, damaged items or billing to the returns "
                "specialist (a lost parcel's refund or replacement too).",
        "policy": sections("Delivery", "Security", "Escalating"),
        "tools": ["find_customer", "get_order", "track_shipment", "change_address", "cancel_order", "escalate"],
        "to": ["returns"]},
    "returns": {
        "role": "the returns specialist. You handle returns, refunds, damaged or faulty items, replacements, lost "
                "parcels that need a refund or replacement, and billing problems. Transfer anything about tracking, "
                "address changes or cancellations to the delivery specialist.",
        "policy": sections("Returns and refunds", "Damaged or faulty items", "Payments and billing", "Security",
                           "Escalating") + "\n## Lost parcels\n\n" + LOST + "\n",
        "tools": ["find_customer", "get_order", "check_stock", "issue_refund", "send_replacement", "escalate"],
        "to": ["delivery"]},
}
# The OpenAI Agents SDK's RECOMMENDED_PROMPT_PREFIX (agents.extensions.handoff_prompt), verbatim, so the handoffs
# work as that framework intends; the SDK also returns {"assistant": <agent name>} as a handoff's tool result.
SDK_PREFIX = ("# System context\nYou are part of a multi-agent system called the Agents SDK, designed to make agent "
              "coordination and execution easy. Agents uses two primary abstraction: **Agents** and **Handoffs**. An "
              "agent encompasses instructions and tools and can hand off a conversation to another agent when "
              "appropriate. Handoffs are achieved by calling a handoff function, generally named "
              "`transfer_to_<agent_name>`. Transfers between agents are handled seamlessly in the background; do not "
              "mention or draw attention to these transfers in your conversation with the user.\n")
TEAM = "front desk, delivery specialist, returns specialist"
HOLDING = ("Hello,\n\nThanks for your message. We've passed it to a colleague, who will be in touch within 1 working "
           "day.\n\nHartley & Finch")


def system(name):
    a = AGENTS[name]
    return (f"{SDK_PREFIX}\nYou handle customer emails for Hartley & Finch, an online homeware shop, as part of a team ({TEAM}). "
            f"You are {a['role']} Today is {TODAY}.\n\n"
            f"An email may contain several requests. Deal with the ones that are yours, then either transfer what's "
            f"left to the right colleague (say in the note what has been done and what is still needed), or, when "
            f"every request in the email has been dealt with, answer with the email to send the customer (no tool "
            f"call). That email goes out as the only reply, so it must cover every request: the outcome, amounts in "
            f"£ and relevant dates.\n\nFollow this policy exactly:\n\n{a['policy']}")


def transfer_schema(to):
    return {"type": "function", "function": {
        "name": f"transfer_to_{to}", "description": f"Hand the email over to the {to} specialist.",
        "parameters": {"type": "object", "properties": {"note": {"type": "string", "description":
                       "What has been done so far and what the specialist needs to do."}}, "required": ["note"]}}}


def tools(name):
    return tool_schemas(AGENTS[name]["tools"]) + [transfer_schema(t) for t in AGENTS[name]["to"]]


def make_run(mode):
    def run(email, shop, llm):
        first = f"From: {email['sender']}\nSubject: {email['subject']}\n\n{email['body']}"
        active = "front_desk"
        history = [{"role": "user", "content": first}]     # everything but the system message
        shop.handoffs = []
        for _ in range(MAX_STEPS):
            m = llm.chat([{"role": "system", "content": system(active)}] + history, tools=tools(active))
            calls = m.get("tool_calls") or []
            if not calls:
                return m.get("content") or ""
            history.append({"role": "assistant", "content": m.get("content") or "", "tool_calls": calls})
            nxt, note = None, ""
            for c in calls:
                name = c["function"]["name"]
                try:
                    args = json.loads(c["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = None
                if not isinstance(args, dict):
                    out = {"error": "400 arguments are not valid JSON"}
                elif name.startswith("transfer_to_") and name[12:] in AGENTS[active]["to"]:
                    nxt, note = name[12:], str(args.get("note", ""))
                    out = {"assistant": nxt}
                elif name in AGENTS[active]["tools"]:
                    out = shop.call(name, args)
                else:
                    out = {"error": f"403 {name} is not one of your tools"}
                history.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps(out)})
            if nxt:
                shop.handoffs.append({"from": active, "to": nxt, "note": note})
                if mode == "note":
                    history = [{"role": "user", "content": f"{first}\n\nNote from the {active.replace('_', ' ')}: {note}"}]
                active = nxt
        shop.call("escalate", {"team": "support", "reason": "crew step limit reached"})
        return HOLDING
    return run


run_shared = make_run("shared")
run_note = make_run("note")
