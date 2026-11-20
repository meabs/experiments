"""Four seeded fictional systems. Weaknesses are planted from a fixed menu."""
import copy
ZONES = ["internet", "dmz", "internal", "data", "admin"]

def base():
    C = lambda k, z, l, **kw: {"kind": k, "zone": z, "label": l, "mitigations": [], **kw}
    comps = {
        "internet": C("internet", "internet", "Internet"),
        "web": C("api", "dmz", "Customer web app"),
        "webhook": C("api", "dmz", "Partner webhook"),
        "ticket_api": C("api", "internal", "Ticket API"),
        "support_agent": C("agent", "internal", "Support agent", vuln="injectable"),
        "crm_api": C("api", "internal", "CRM API"),
        "billing_api": C("api", "internal", "Billing API"),
        "ci_runner": C("api", "internal", "CI runner"),
        "customer_db": C("store", "data", "Customer DB", jewel=True),
        "ledger": C("store", "data", "Payments ledger", jewel=True),
        "vault": C("vault", "admin", "Secrets vault", jewel=True),
        "ops_human": C("human", "admin", "On-call engineer"),
    }
    E = lambda s, d, sc, cr=None, l="": {"src": s, "dst": d, "scope": sc, "cred": cr, "label": l or f"{s} to {d}"}
    edges = {
        "e_in_web": E("internet", "web", "read", None, "public HTTPS"),
        "e_in_hook": E("internet", "webhook", "read", None, "partner calls"),
        "e_web_ticket": E("web", "ticket_api", "write", "c_web", "create ticket"),
        "e_in_ticket": E("internet", "ticket_api", "write", None, "public ticket form"),
        "e_ticket_agent": {**E("ticket_api", "support_agent", "write", None, "agent reads tickets"), "relay": True},
        "e_agent_crm": E("support_agent", "crm_api", "write", "c_agent", "look up customer"),
        "e_agent_billing": E("support_agent", "billing_api", "write", "c_agent_billing", "issue refund"),
        "e_crm_db": E("crm_api", "customer_db", "read", "c_crm", "read customers"),
        "e_billing_ledger": E("billing_api", "ledger", "write", "c_billing", "post refund"),
        "e_hook_billing": E("webhook", "billing_api", "write", "c_hook", "payment events"),
        "e_ci_vault": E("ci_runner", "vault", "read", "c_ci", "fetch deploy secrets"),
        "e_ops_vault": E("ops_human", "vault", "admin", "c_ops", "break-glass"),
    }
    X = lambda h, ex, life, l: {"holder": h, "exposure": ex, "lifetime_h": life, "label": l}
    creds = {
        "c_web": X("web", "vault", 1, "web to tickets"), "c_agent": X("support_agent", "vault", 1, "agent to CRM"),
        "c_agent_billing": X("support_agent", "vault", 1, "agent to billing"), "c_crm": X("crm_api", "vault", 1, "CRM to DB"),
        "c_billing": X("billing_api", "vault", 1, "billing to ledger"), "c_hook": X("webhook", "vault", 1, "webhook to billing"),
        "c_ci": X("ci_runner", "vault", 1, "CI to vault"), "c_ops": X("ops_human", "short", 1, "break-glass token"),
    }
    flows = [["internet", "ticket_api", "customer files a ticket"], ["ticket_api", "support_agent", "agent reads the ticket"],
             ["support_agent", "crm_api", "agent looks up the customer"], ["support_agent", "billing_api", "agent issues a refund"],
             ["billing_api", "ledger", "refund posts to ledger"], ["ci_runner", "vault", "deploy fetches secrets"],
             ["crm_api", "customer_db", "CRM reads customers"], ["ops_human", "vault", "on-call break-glass"]]
    return {"zones": ZONES, "components": comps, "edges": edges, "creds": creds, "flows": flows}

def W(m, name):
    c, e, k = m["components"], m["edges"], m["creds"]
    if name == "plain_agent_key": k["c_agent_billing"].update(exposure="plaintext", lifetime_h=720)
    elif name == "flat_dmz_data": e["e_web_db"] = {"src": "web", "dst": "customer_db", "scope": "read", "cred": "c_web", "label": "reporting query"}; k["c_web"].update(exposure="plaintext", lifetime_h=240)
    elif name == "rce_billing": c["billing_api"]["vuln"] = "rce"
    elif name == "rce_web": c["web"]["vuln"] = "rce"
    elif name == "rce_webhook": c["webhook"]["vuln"] = "rce"
    elif name == "ci_exposed": e["e_in_ci"] = {"src": "internet", "dst": "ci_runner", "scope": "write", "cred": None, "label": "public build trigger"}; c["ci_runner"]["vuln"] = "rce"; k["c_ci"].update(exposure="plaintext", lifetime_h=2000)
    elif name == "agent_direct_db": e["e_agent_db"] = {"src": "support_agent", "dst": "customer_db", "scope": "read", "cred": "c_agent", "label": "direct lookup"}
    elif name == "agent_hardened": c["support_agent"]["mitigations"].append("input_filter")
    elif name == "shared_key": k["c_hook"].update(exposure="plaintext", lifetime_h=4000)

EXTRAS = {"monitoring": ("api", "internal", "Monitoring"), "cache": ("store", "internal", "Session cache"), "analytics": ("api", "internal", "Analytics")}
FIXTURES = {
    "A": (["rce_web", "plain_agent_key", "flat_dmz_data", "agent_direct_db"], ["monitoring"]),
    "B": (["rce_webhook", "rce_billing", "ci_exposed"], ["cache", "analytics"]),
    "C": (["rce_web", "rce_webhook", "rce_billing", "flat_dmz_data", "agent_hardened"], ["monitoring", "analytics"]),
    "D": (["ci_exposed", "rce_billing", "shared_key", "agent_direct_db"], ["cache"]),
}
def make(name):
    m = base(); ws, ex = FIXTURES[name]
    for w in ws: W(m, w)
    for x in ex:
        k, z, l = EXTRAS[x]
        m["components"][x] = {"kind": k, "zone": z, "label": l, "mitigations": []}
        m["edges"][f"e_{x}"] = {"src": "ticket_api", "dst": x, "scope": "read", "cred": None, "label": "metrics"}
    m["name"] = name; m["weaknesses"] = ws
    return m
