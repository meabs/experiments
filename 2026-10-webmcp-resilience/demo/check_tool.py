"""Runs WebMCP Resilience on one version of one app: the app folder, with an optional overlay of changed files (a fix)
laid over a copy. Serves it on a free port, writes .webmcp/config.yaml (base_url and the app's state script from
demo/state/<app>.js), and runs every scenario in demo/scenarios/<app>/ with `webmcp run --ci --json --allow-mutations`.
Prints one JSON line: {scenario: {"pass": bool, "detail": str}}. Usage: check_tool.py <app> [overlay] [--keep DIR]
"""
import contextlib, functools, glob, http.server, json, os, shutil, subprocess, sys, tempfile, threading

D = os.path.dirname(os.path.abspath(__file__))
E = os.path.dirname(D)
WEBMCP = os.environ.get("WEBMCP_BIN", os.path.expanduser("~/code/benchmark/webmcp-exp/env-tool/bin/webmcp"))


READY = ("await new Promise((resolve) => { const t = setInterval(async () => { if ((await document.modelContext.getTools())"
         ".length) { clearInterval(t); resolve(); } }, 20); })")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


@contextlib.contextmanager
def serve(folder):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=folder))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield srv.server_address[1]
    finally:
        srv.shutdown()


def check(app, overlay=None, keep=None):
    tmp = tempfile.mkdtemp()
    ws = os.path.join(tmp, "app")
    shutil.copytree(os.path.join(E, "apps", app), ws, symlinks=False)
    shared = os.path.join(E, "apps", "_shared")
    for f in os.listdir(shared):  # the apps link their shared files; serve real copies
        p = os.path.join(ws, f)
        if os.path.islink(p) or not os.path.exists(p):
            if os.path.lexists(p):
                os.remove(p)
            shutil.copy(os.path.join(shared, f), p)
    if overlay:
        shutil.copytree(overlay, ws, dirs_exist_ok=True)
    out = {}
    with serve(ws) as port:
        os.makedirs(os.path.join(ws, ".webmcp"), exist_ok=True)
        script = open(os.path.join(D, "state", f"{app}.js")).read().strip()
        with open(os.path.join(ws, ".webmcp", "config.yaml"), "w") as f:
            # `webmcp run` discovers tools straight after loading, with no registration grace (preflight has one); these
            # apps register theirs after their first server calls, so wait for them in the documented setup_script.
            f.write(f"base_url: http://127.0.0.1:{port}\nbrowser: chromium\nstate_script: {json.dumps(script)}\n"
                    f"setup_script: {json.dumps(READY)}\n")
        for sc in sorted(glob.glob(os.path.join(D, "scenarios", app, "*.yaml"))):
            name = os.path.basename(sc)[:-5]
            p = subprocess.run([WEBMCP, "run", sc, "--ci", "--json", "--allow-mutations", "--run-id", name],
                               cwd=ws, capture_output=True, text=True, timeout=300)
            try:
                r = json.loads(p.stdout)
            except json.JSONDecodeError:
                r = {}
            res = r.get("result") if isinstance(r.get("result"), dict) else {}
            code = res.get("error_code") or r.get("error_code")
            # A catch is an invariant violation; anything else that is not a pass is a setup or tool error.
            out[name] = {"pass": p.returncode == 0 and res.get("passed") is True, "code": code,
                         "detail": (res.get("error") or r.get("error") or p.stderr[-300:] or "")[:300]}
    if keep:
        shutil.copytree(os.path.join(ws, ".webmcp"), keep, dirs_exist_ok=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    keep = None
    if "--keep" in args:
        i = args.index("--keep"); keep = args[i + 1]; del args[i:i + 2]
    print(json.dumps(check(args[0], args[1] if len(args) > 1 and args[1] != "-" else None, keep)))
