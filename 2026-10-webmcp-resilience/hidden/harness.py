"""Hidden-test harness for webmcp-resilience. Independent of WebMCP Resilience (the tool under test): plain Playwright.

Serves an app folder on a free local port, opens it in a fresh Chromium context per case with the simulated backend's
latencies and seed data set before the page loads (window.__apiLatency, window.__apiSeed, read by latency.js), and
drives the page the way a person and an assistant would at the same time: WebMCP tool calls through
document.modelContext, and clicks dispatched inside the page at exact offsets. State is read from the simulated
backend (window.__backend.snapshot(), defined in api.js, which agents may not change) and from tool results.
"""
import contextlib, functools, http.server, json, threading, traceback

from playwright.sync_api import sync_playwright

PAGE_JS = """
window.__calls = {};
window.__startCall = async (id, name, args, abortMs) => {
  const tools = await document.modelContext.getTools();
  const tool = tools.find((t) => t.name === name);
  if (!tool) { window.__calls[id] = Promise.resolve({ error: 'NO_TOOL' }); return; }
  const ac = new AbortController();
  if (abortMs != null) setTimeout(() => ac.abort(), abortMs);
  window.__calls[id] = Promise.resolve()
    .then(() => document.modelContext.executeTool(tool, args, { signal: ac.signal }))
    .then((r) => ({ ok: typeof r === 'string' ? JSON.parse(r) : r }), (e) => ({ error: String((e && e.name) || e) }));
};
"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


@contextlib.contextmanager
def serve(folder):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=folder))
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}/"
    finally:
        srv.shutdown()


class Page:
    def __init__(self, browser, url, latency=None, seed=None):
        self.ctx = browser.new_context()
        self.page = self.ctx.new_page()
        self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        init = f"window.__apiLatency = {json.dumps(latency or {})}; window.__apiSeed = {json.dumps(seed or {})};"
        self.page.add_init_script(init)
        self.page.goto(url)
        self._ready()
        self.n = 0

    def _ready(self):
        self.page.wait_for_function("() => window.__app && window.__backend && document.modelContext", timeout=10000)
        self.page.wait_for_function("async () => (await document.modelContext.getTools()).length > 0", timeout=10000)
        self.page.wait_for_timeout(400)  # initial loads (default latency 120 ms per call) finish
        self.page.evaluate(PAGE_JS)

    def reload(self):
        """Reloads the page, as a customer pressing refresh. Calls still running in the old page are lost."""
        self.page.reload()
        self._ready()

    def call(self, name, args=None, at=0, abort_ms=None):
        """Starts a tool call `at` ms from now (in the page); returns its id. abort_ms: cancel it that long after start."""
        self.n += 1
        cid = f"c{self.n}"
        self.page.evaluate("([id, name, args, at, abortMs]) => { window.__calls[id] = new Promise((res) => setTimeout(() =>"
                           " { window.__startCall(id, name, args, abortMs).then(() => res(window.__calls[id])); }, at)); }",
                           [cid, name, args or {}, at, abort_ms])
        return cid

    def click(self, selector, at=0):
        """Clicks an element `at` ms from now, inside the page (as a person's click, with exact timing)."""
        self.page.evaluate("([sel, at]) => setTimeout(() => document.querySelector(sel).click(), at)", [selector, at])

    def eval(self, js, arg=None):
        return self.page.evaluate(js, arg)

    def fill(self, selector, value):
        self.page.fill(selector, value)

    def result(self, cid, timeout=15000):
        return self.page.evaluate("async ([id, t]) => { const deadline = Date.now() + t;"
                                  " while (!window.__calls[id] && Date.now() < deadline) await new Promise((r) => setTimeout(r, 10));"
                                  " return await Promise.race([window.__calls[id], new Promise((r) => setTimeout(() => r({ error: 'TIMEOUT' }), t))]); }",
                                  [cid, timeout])

    def settle(self, ms=1500):
        self.page.wait_for_timeout(ms)

    def backend(self):
        return self.page.evaluate("() => window.__backend.snapshot()")

    def tools(self):
        return self.page.evaluate("async () => (await document.modelContext.getTools()).map((t) => t.name)")

    def text(self, selector):
        return self.page.inner_text(selector)

    def close(self):
        self.ctx.close()


def run(folder, cases):
    """cases: list of (name, fn(open_page) -> (ok, detail)). Prints one JSON summary; returns True if all passed."""
    results = []
    with serve(folder) as url, sync_playwright() as p:
        browser = p.chromium.launch()
        opened = []

        def open_page(latency=None, seed=None):
            pg = Page(browser, url, latency, seed)
            opened.append(pg)
            return pg

        for name, fn in cases:
            try:
                ok, detail = fn(open_page)
            except Exception as e:  # a crash in the app or a missing tool counts as a failed case
                ok, detail = False, f"{type(e).__name__}: {e}".splitlines()[0][:300]
                traceback.print_exc()
            errs = [e for pg in opened for e in pg.errors]
            for pg in opened:
                pg.close()
            opened.clear()
            if errs:
                detail = f"{detail}; page errors: {errs[:2]}"
            results.append({"case": name, "passed": bool(ok), "detail": detail})
        browser.close()
    passed = sum(r["passed"] for r in results)
    print(json.dumps({"passed": passed, "total": len(results), "cases": results}, indent=1))
    return passed == len(results)
