"""Arms B (specialist agent), C (specialist team as a Strands Graph) and D (the same team as a Strands Swarm), built
with Strands Agents on OpenRouter.

Usage (run with the Strands venv):  python -I reviewers.py <specialist|team|swarm> <model> <repo> <app url> <out dir>
The repo dir is this run's private copy of the target app; the app is already running at <app url> (started by
run.py). Writes <out dir>/FINDINGS.json (via the submit_findings tool), <out dir>/transcript.json and
<out dir>/usage.json.
"""
import json, os, re, sys, time
from pathlib import Path

import requests
from strands import Agent, tool
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.hooks import AfterToolCallEvent, BeforeInvocationEvent, BeforeToolCallEvent, HookProvider
from strands.models.openai_responses import OpenAIResponsesModel
from strands.multiagent import GraphBuilder, Swarm

HERE = Path(__file__).resolve().parent
PROMPTS = HERE.parent / "prompts"
TASK = (PROMPTS / "task.md").read_text().strip()
CHECKLIST = (PROMPTS / "specialist.md").read_text().strip()
MAX_READ = 400          # lines per read_file call
MAX_OUT = 20000         # characters returned by any tool


def make_tools(repo: Path, app_url: str, out: Path):
    repo = repo.resolve()

    def inside(rel):
        p = (repo / rel).resolve()
        if p != repo and repo not in p.parents:
            raise ValueError("path is outside the repository")
        return p

    @tool
    def list_files(path: str = ".") -> str:
        """List the files under a directory of the repository (recursive), with their sizes in lines.

        Args:
            path: directory relative to the repository root
        """
        base = inside(path)
        rows = []
        for p in sorted(base.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and ".git" not in p.parts:
                try:
                    n = sum(1 for _ in p.open(errors="replace"))
                except OSError:
                    n = 0
                rows.append(f"{p.relative_to(repo)}  ({n} lines)")
        return "\n".join(rows)[:MAX_OUT] or "(empty)"

    @tool
    def read_file(path: str, start_line: int = 1, end_line: int = 0) -> str:
        """Read a text file from the repository, with line numbers.

        Args:
            path: file path relative to the repository root
            start_line: first line to return (1-based)
            end_line: last line to return; 0 means up to 400 lines from start_line
        """
        lines = inside(path).read_text(errors="replace").splitlines()
        start = max(1, start_line)
        end = end_line if end_line else start + MAX_READ - 1
        end = min(end, len(lines), start + MAX_READ - 1)
        return "\n".join(f"{i:4d}  {lines[i - 1]}" for i in range(start, end + 1))[:MAX_OUT] or "(no lines)"

    @tool
    def search_code(pattern: str, path: str = ".") -> str:
        """Search the repository's files for a regular expression; returns file:line: text for each match.

        Args:
            pattern: Python regular expression
            path: directory or file relative to the repository root
        """
        rx = re.compile(pattern)
        base = inside(path)
        files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        hits = []
        for p in files:
            if "__pycache__" in p.parts or ".git" in p.parts:
                continue
            for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{p.relative_to(repo)}:{i}: {line.strip()}")
        return "\n".join(hits)[:MAX_OUT] or "(no matches)"

    @tool
    def http_request(method: str, path: str, json_body: str = "", headers: str = "", cookies: str = "") -> str:
        """Send an HTTP request to the copy of the application running on localhost, and return the status,
        headers and body. Only this local copy can be reached.

        Args:
            method: GET, POST, PUT, PATCH or DELETE
            path: path and query string, e.g. /products?sort=name
            json_body: request body as a JSON string (sent as application/json), or empty
            headers: extra headers as a JSON object string, e.g. {"Authorization": "Bearer ..."}, or empty
            cookies: cookies as a JSON object string, or empty
        """
        if not path.startswith("/"):
            return "error: path must start with /"
        try:
            r = requests.request(method.upper(), app_url + path, timeout=15, allow_redirects=False,
                                 json=json.loads(json_body) if json_body else None,
                                 headers=json.loads(headers) if headers else None,
                                 cookies=json.loads(cookies) if cookies else None)
        except Exception as e:
            return f"error: {type(e).__name__}: {e}"
        head = "\n".join(f"{k}: {v}" for k, v in r.headers.items())
        return f"HTTP {r.status_code}\n{head}\n\n{r.text}"[:MAX_OUT]

    @tool
    def submit_findings(findings_json: str) -> str:
        """Write the final findings to FINDINGS.json. Call once, at the end, with the complete list.

        Args:
            findings_json: a JSON list of objects with keys file, line, category, title, description, evidence
        """
        if (out / "FINDINGS.json").exists():
            return "error: findings were already submitted; only the first submission counts"
        try:
            data = json.loads(findings_json)
            assert isinstance(data, list) and all(isinstance(f, dict) for f in data)
        except Exception:
            return "error: findings_json must be a JSON list of objects; nothing was written"
        (out / "FINDINGS.json").write_text(json.dumps(data, indent=1))
        return f"wrote {len(data)} findings to FINDINGS.json"

    return [list_files, read_file, search_code, http_request], submit_findings


def model(model_id, parallel=True):
    key = Path.home().joinpath(".config/openrouter.key").read_text().strip()
    # The Responses API keeps the model's reasoning between turns, as Codex does; same reasoning effort as Codex.
    return OpenAIResponsesModel(client_args={"api_key": key, "base_url": "https://openrouter.ai/api/v1"},
                                model_id=model_id, params={"reasoning": {"effort": "medium"},
                                                           **({} if parallel else {"parallel_tool_calls": False})})


def context(app_url):
    return (f"The repository is the current project. A copy of the application is running at {app_url} (paths "
            f"start with /); you can reach it with the http_request tool. Today is {time.strftime('%Y-%m-%d')}.")


class ToolLog(HookProvider):
    """Appends every tool call (agent, tool, input) to <out>/tools.jsonl."""
    def __init__(self, path):
        self.path = path

    def register_hooks(self, registry, **kw):
        registry.add_callback(BeforeToolCallEvent, self.log)

    def log(self, event):
        with open(self.path, "a") as f:
            f.write(json.dumps({"t": round(time.time(), 1), "agent": event.agent.name,
                                "tool": event.tool_use["name"], "input": event.tool_use["input"]}, default=str) + "\n")


class HandoffEndsTurn(HookProvider):
    """In Strands' Swarm the handoff tool only records the next agent; the agent keeps going and the last handoff
    wins. In the pilot that left agents handing off to everyone, repeatedly. As in OpenAI's Swarm, a handoff here
    ends the agent's turn (after the current tool calls), and a second handoff in the same turn is refused."""
    def __init__(self):
        self.done = False

    def register_hooks(self, registry, **kw):
        registry.add_callback(BeforeInvocationEvent, self.reset)
        registry.add_callback(BeforeToolCallEvent, self.before)
        registry.add_callback(AfterToolCallEvent, self.after)

    def reset(self, event):
        self.done = False

    def before(self, event):
        if event.tool_use["name"] == "handoff_to_agent" and self.done:
            event.cancel_tool = "Not done: you have already handed off in this turn. Finish your turn now."

    def after(self, event):
        if event.tool_use["name"] == "handoff_to_agent" and not self.done:
            self.done = True
            event.agent.cancel(after_current_tools=True)


def memory():
    """Strands' default keeps the last 40 messages, which dropped the task (and the swarm's handoff message) from a
    long review in the pilot, and the agent started over in a loop. Keep the first message and a larger window."""
    return SlidingWindowConversationManager(window_size=300, pin_first=1)


SWARM_ROLES = {}
for block in (PROMPTS / "swarm.md").read_text().split("\n\n")[1:]:
    name, _, text = block.partition(":")
    SWARM_ROLES[name.strip()] = " ".join(text.split())


TEAM_ROLES = {}
for block in (PROMPTS / "team.md").read_text().split("\n\n")[1:]:
    name, _, text = block.partition(":")
    TEAM_ROLES[name.strip()] = " ".join(text.split())
SPECIALISTS = ["injection", "access_auth", "crypto_config_deps", "logic_integrity_errors"]


def usage_of(agents):
    u = {"input": 0, "cached": 0, "output": 0, "total": 0, "cycles": 0}
    for a in agents:
        acc = a.event_loop_metrics.accumulated_usage
        u["input"] += acc.get("inputTokens", 0); u["output"] += acc.get("outputTokens", 0)
        u["cached"] += acc.get("cacheReadInputTokens", 0)
        u["total"] += acc.get("totalTokens", 0); u["cycles"] += a.event_loop_metrics.cycle_count
    return u


def run(arm, model_id, repo, app_url, out):
    out.mkdir(parents=True, exist_ok=True)
    tools, submit = make_tools(repo, app_url, out)
    t0 = time.time()
    if arm == "specialist":
        agent = Agent(model=model(model_id), tools=tools + [submit], callback_handler=None, name="specialist",
                      conversation_manager=memory(), hooks=[ToolLog(out / "tools.jsonl")],
                      system_prompt=CHECKLIST + "\n\n" + context(app_url) +
                      "\n\nWhen you have finished, call submit_findings with the complete list.")
        agent(TASK)
        agents, extra = [agent], {}
    elif arm == "team":
        agents = {}
        for name, role in TEAM_ROLES.items():
            agents[name] = Agent(model=model(model_id), name=name, callback_handler=None, conversation_manager=memory(),
                                 hooks=[ToolLog(out / "tools.jsonl")],
                                 tools=tools + ([submit] if name == "verifier" else []),
                                 system_prompt=f"{CHECKLIST}\n\nYour role in the team: {role}\n\n{context(app_url)}")
        g = GraphBuilder()
        for name, a in agents.items():
            g.add_node(a, name)
        g.set_entry_point("recon")

        def all_specialists_done(state):
            return set(SPECIALISTS) <= {n.node_id for n in state.completed_nodes}

        for sp in SPECIALISTS:
            g.add_edge("recon", sp)
            g.add_edge(sp, "verifier", condition=all_specialists_done)
        g.set_execution_timeout(2400); g.set_node_timeout(1200)
        res = g.build()(TASK)
        agents = list(agents.values())
        extra = {"status": str(res.status), "order": [n.node_id for n in res.execution_order]}
    else:
        agents = []
        for name, role in SWARM_ROLES.items():
            # One tool call per step: Strands' Swarm runs one agent at a time, and in the pilot a recon agent that
            # handed off to all five colleagues in one parallel step left the swarm looping.
            agents.append(Agent(model=model(model_id, parallel=False), name=name, callback_handler=None, conversation_manager=memory(),
                                hooks=[ToolLog(out / "tools.jsonl"), HandoffEndsTurn()],
                                tools=tools + ([submit] if name == "verifier" else []),
                                description=role.split(".")[0],
                                system_prompt=f"{CHECKLIST}\n\nYour role in the team: {role}\n\n{context(app_url)}" +
                                ("\n\nWhen you have finished, call submit_findings with the complete list."
                                 if name == "verifier" else "")))
        swarm = Swarm(agents, entry_point=agents[0], max_handoffs=12, max_iterations=14, execution_timeout=2400,
                      node_timeout=1200)
        res = swarm(TASK)
        extra = {"status": str(res.status), "handoffs": [n.node_id for n in res.node_history]}
    secs = time.time() - t0
    (out / "transcript.json").write_text(json.dumps({a.name: a.messages for a in agents}, indent=1, default=str))
    (out / "usage.json").write_text(json.dumps({"arm": arm, "model": model_id, "seconds": round(secs, 1),
                                                **usage_of(agents), **extra}, indent=1))


if __name__ == "__main__":
    arm, model_id, repo, app_url, out = sys.argv[1:6]
    run(arm, model_id, Path(repo), app_url, Path(out))
