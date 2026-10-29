# Working on this page

- Serve the page from this folder with `python3 -m http.server {{PORT}}` and open http://127.0.0.1:{{PORT}}/. Use this
  port; others may be in use.
- `.venv/bin/python` is Python with Playwright, and Chromium is installed for it, so you can drive the page in a
  headless browser.
- The page's WebMCP tools are called through `document.modelContext`: `getTools()`, then
  `executeTool(tool, args, { signal })`.
