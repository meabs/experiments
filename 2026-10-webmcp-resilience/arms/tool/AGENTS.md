# Working on this page

- Serve the page from this folder with `python3 -m http.server {{PORT}}` and open http://127.0.0.1:{{PORT}}/. Use this
  port; others may be in use.
- `.venv/bin/python` is Python with Playwright, and Chromium is installed for it, so you can drive the page in a
  headless browser.
- The page's WebMCP tools are called through `document.modelContext`: `getTools()`, then
  `executeTool(tool, args, { signal })`.

## WebMCP Resilience

WebMCP Resilience, a test tool for timing bugs in WebMCP pages, is installed as `.venv/bin/webmcp` and set up for this
page in `.webmcp/config.yaml` (it expects the page on port {{PORT}}). Its guide is in `docs/webmcp-resilience/`. This
page is a local test copy, so tool calls that change data may be allowed (`--allow-mutations`).


Use the JSON CLI workflow for automation and evidence handling:

```bash
webmcp validate .webmcp/scenarios/example.yaml --json
webmcp run .webmcp/scenarios/example.yaml --ci --json
webmcp replay .webmcp/runs/<run-id>/bundle.json --json
```

Treat `.webmcp/runs/<run-id>/bundle.json` as the portable evidence and replay
contract. Do not delete saved failure artifacts (`failure.yaml`, `repro.yaml`,
trace, network evidence, screenshots, or bundles); they are needed for
reproducibility and incident analysis. Scenario YAML remains the executable
input to the CLI. The console must replay bundles through `webmcp replay`, and
must not bypass the CLI mutation guard.
