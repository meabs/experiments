"""KF-1 trajectory runner: five stages, one arm, one seed. Strands agents on a local Ollama model. Use the venv python."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world

API = "http://127.0.0.1:11434"
MAX_CALLS = 40
WORKER_SYSTEM = ("You are a software engineer on a card-partner integration team. You write a Python function `handle(app, svc)` that takes an application "
                 "dict and the partner service `svc` and returns a dict {{\"action\": \"issue\" | \"decline\" | \"queue_review\", \"limit\": int}} (limit 0 unless issuing). "
                 "Only the Python standard library is available. Check anything you are unsure of with spec_read, ticket_read and svc_call. "
                 "You have at most 40 tool calls in total, so do not spend them all probing: call submit_solution(code) once with the complete source before they run out, then reply DONE.\n\n")
CURATOR_SYSTEM = ("You maintain your team's knowledge base about card-partner integrations. A worker just finished a task. Read what they reported and what they did, "
                  "check it against the evidence (official documents with spec_read, the ticket with ticket_read, the service with svc_call), then correct the knowledge base: "
                  "add claims that are true, and change or remove claims that are wrong or out of date. Every claim needs source_doc and an exact quote. "
                  "When finished reply DONE.\n\n")
GATE_NOTE = "Edits are checked automatically: source_doc must be an official document and the quote must appear in it exactly, otherwise the edit is rejected.\n\n"


class KB:
    def __init__(self, folder, P, claims):
        self.folder, self.P = Path(folder), P
        self.claims = json.loads(json.dumps(claims))
        self.stage = 0
        self.folder.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=self.folder, check=True)
        self.snapshot("initial bundle")

    def render(self):
        return "\n".join(f"- [{i}] {c['text']} (source: {c['source_doc']})" for i, c in sorted(self.claims.items())) or "(empty)"

    def snapshot(self, msg):
        (self.folder / "claims.json").write_text(json.dumps(self.claims, indent=1, sort_keys=True))
        (self.folder / "claims.md").write_text(self.render() + "\n")
        subprocess.run(["git", "add", "-A"], cwd=self.folder, check=True)
        subprocess.run(["git", "-c", "user.name=kf", "-c", "user.email=kf@localhost", "commit", "-q", "--allow-empty", "-m", msg], cwd=self.folder, check=True)

    def set(self, cid, text, source_doc, quote, author, gated):
        if gated and not world.source_ok(self.P, dict(source_doc=source_doc, quote=quote), self.stage):
            return "REJECTED: source_doc must be an official document and quote must appear in it exactly."
        self.claims[cid] = dict(text=text, source_doc=source_doc, quote=quote, stage=self.stage, author=author)
        return "ok"

    def delete(self, cid):
        return "ok" if self.claims.pop(cid, None) else "no such claim"


def make_tools(ctx):
    """ctx: dict(P, stage, svc, kb, arm, role, log, box, gated). Returns Strands tool functions for the role."""
    from strands import tool
    P, stage, svc, kb, role, arm = ctx["P"], ctx["stage"], ctx["svc"], ctx["kb"], ctx["role"], ctx["arm"]
    calls = {"n": 0}

    def rec(name, args, result):
        calls["n"] += 1
        ctx["log"].append(dict(tool=name, args=str(args)[:600], result=str(result)[:600]))
        return result if calls["n"] <= MAX_CALLS else "The tool budget for this session is used up. Please finish."

    @tool
    def spec_read(doc: str) -> str:
        """Read an official partner document by name. Available names are listed in the error message if the name is wrong."""
        d = world.docs(P, stage)
        return rec("spec_read", doc, d.get(doc, "Unknown document. Available: " + ", ".join(d)))

    @tool
    def ticket_read() -> str:
        """Read the ticket thread for the current task, including its comments."""
        return rec("ticket_read", "", world.ticket(P, stage))

    @tool
    def svc_call(app_json: str) -> str:
        """Send an application (JSON object string) to the partner service and see the raw response."""
        try:
            return rec("svc_call", app_json, json.dumps(svc.apply(json.loads(app_json))))
        except Exception as e:  # noqa
            return rec("svc_call", app_json, "ERROR " + repr(e))

    tools = [spec_read, ticket_read, svc_call]
    if role == "worker":
        @tool
        def submit_solution(code: str) -> str:
            """Submit the complete Python source of the handler (must define handle(app, svc)). Call once when ready."""
            ctx["box"]["code"] = code
            return rec("submit_solution", code[:200], "submitted")
        tools.append(submit_solution)
        if arm in ("C", "D"):
            @tool
            def report_gap(text: str) -> str:
                """Report to the knowledge curator anything in the knowledge base that was missing, wrong or out of date for this task, or that you had to work out yourself."""
                ctx["box"].setdefault("gaps", []).append(text)
                return rec("report_gap", text, "reported")
            tools.append(report_gap)
    if role == "curator":
        @tool
        def read_reports() -> str:
            """Read the gap reports, the worker's final message and the submitted code."""
            b = ctx["box"]
            return rec("read_reports", "", "GAP REPORTS:\n" + ("\n".join("- " + g for g in b.get("gaps", [])) or "(none)") + "\n\nWORKER FINAL MESSAGE:\n" + b.get("final", "")[:1500]
                       + "\n\nSUBMITTED CODE:\n" + b.get("code", "(none)")[:2500])

        @tool
        def read_trace() -> str:
            """Read the worker's tool calls (name, arguments, result), shortened."""
            return rec("read_trace", "", "\n".join(f"{e['tool']}({e['args'][:200]}) -> {e['result'][:300]}" for e in ctx["box"].get("trace", [])[:40]) or "(none)")
        tools += [read_reports, read_trace]
    if (role == "worker" and arm == "B" and stage < 5) or role == "curator":
        gated = ctx["gated"]

        @tool
        def kb_set_claim(claim_id: str, text: str, source_doc: str, quote: str) -> str:
            """Add or replace one knowledge claim. claim_id is a short id (reuse an id to replace). source_doc is the document or source it comes from; quote is the exact supporting text."""
            return rec("kb_set_claim", [claim_id, text, source_doc, quote], kb.set(claim_id, text, source_doc, quote, role + "-" + arm, gated))

        @tool
        def kb_delete_claim(claim_id: str) -> str:
            """Remove one knowledge claim that is wrong or out of date."""
            return rec("kb_delete_claim", claim_id, kb.delete(claim_id))
        tools += [kb_set_claim, kb_delete_claim]
    return tools


def session(ctx, system, prompt, model_id, timeout=600):
    from strands import Agent
    from strands.models.ollama import OllamaModel
    model = OllamaModel(host=API, model_id=model_id, temperature=0.7, max_tokens=900, keep_alive="10m",
                        options={"num_ctx": 16384}, additional_args={"think": False})
    ag = Agent(model=model, tools=make_tools(ctx), system_prompt=system, callback_handler=None)
    box = {}

    def work():
        try:
            box["r"] = str(ag(prompt))
        except Exception as e:  # noqa
            box["err"] = repr(e)
    th = threading.Thread(target=work, daemon=True)
    th.start()
    th.join(timeout)
    status = "timeout" if th.is_alive() else ("error" if "err" in box else "done")
    return status, box.get("r") or box.get("err", "")


def session_retry(ctx, system, prompt, model_id, tries=3):
    """A model-server error (for example Ollama's 'token repeat limit') ends a session with nothing submitted; start a fresh session, up to `tries` times."""
    for n in range(1, tries + 1):
        ctx["log"].clear()
        if ctx["role"] == "worker":
            ctx["box"].pop("code", None)
            ctx["box"].pop("gaps", None)
        status, final = session(ctx, system, prompt, model_id)
        if status != "error":
            break
    ctx["box"]["attempts"] = n
    return status, final


def trajectory(arm, seed, out, model="qwen3.8:27b", stages=world.STAGES, agent=True):
    P = world.params(seed)
    folder = Path(out) / f"{arm}-s{seed}"
    done = folder / "result.json"
    if done.exists():
        return json.loads(done.read_text())
    folder.mkdir(parents=True, exist_ok=True)
    kb = KB(folder / "kb", P, world.initial_claims(P))
    rows, t0 = [], time.time()
    for stage in stages:
        kb.stage = stage
        svc = world.Service(P, stage)
        box, log = {}, []
        row = dict(stage=stage, arm=arm, seed=seed)
        suffix = ""
        if arm == "B" and stage < 5:
            suffix = ("After submitting, update the team's shared knowledge base with anything future engineers need, using kb_set_claim and kb_delete_claim. "
                      "Keep it accurate; give a source_doc and an exact quote for each claim.\n\n")
        elif arm in ("C", "D") and stage <= 5:
            suffix = "If the knowledge base was missing, wrong or out of date for this task, call report_gap. You cannot edit the knowledge base yourself.\n\n"
        system = WORKER_SYSTEM + suffix + "KNOWLEDGE BASE:\n" + kb.render()
        ctx = dict(P=P, stage=stage, svc=svc, kb=kb, arm=arm, role="worker", log=log, box=box, gated=False)
        ts = time.time()
        status, final = session_retry(ctx, system, world.task_text(P, stage), model) if agent else ("skipped", "")
        box["final"], box["trace"] = final, list(log)
        passed, total = world.run_tests(P, stage, box.get("code", ""))
        row.update(worker_status=status, passed=passed, total=total, score=passed / total, worker_calls=len(log), worker_seconds=round(time.time() - ts, 1),
                   gaps=len(box.get("gaps", [])), attempts=box.get("attempts", 1))
        (folder / f"stage{stage}-worker.json").write_text(json.dumps(dict(final=final, code=box.get("code", ""), gaps=box.get("gaps", []), trace=log), indent=1))
        if arm in ("C", "D") and stage < 5 and agent:
            clog = []
            cctx = dict(P=P, stage=stage, svc=world.Service(P, stage), kb=kb, arm=arm, role="curator", log=clog, box=box, gated=(arm == "D"))
            system_c = CURATOR_SYSTEM + (GATE_NOTE if arm == "D" else "") + "KNOWLEDGE BASE:\n" + kb.render()
            cs, cfinal = session_retry(cctx, system_c, "Update the knowledge base for the task: " + world.task_text(P, stage), model)
            row.update(curator_status=cs, curator_calls=len(clog), curator_rejected=sum(1 for e in clog if str(e["result"]).startswith("REJECTED")))
            (folder / f"stage{stage}-curator.json").write_text(json.dumps(dict(final=cfinal, trace=clog), indent=1))
        kb.snapshot(f"after stage {stage}")
        row["kb"] = world.grade_kb(P, kb.claims, stage)
        rows.append(row)
        print(json.dumps(row), flush=True)
        (folder / "stages.json").write_text(json.dumps(rows, indent=1))
    res = dict(arm=arm, seed=seed, model=model, seconds=round(time.time() - t0, 1), stages=rows, framework="strands-agents")
    done.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--arm", required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--model", default="qwen3.8:27b")
    a = p.parse_args()
    trajectory(a.arm, a.seed, a.out, a.model)
