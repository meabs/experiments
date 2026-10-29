# Edit listing

A marketplace seller's listing page, with **Edit** and **Preview** tabs. Sellers save with the **Save** button, and the
marketplace's AI assistant saves through WebMCP tools (`save_listing` and others). Each tab registers its own WebMCP
tools when it opens and unregisters them when the seller leaves it (see `src/scope.js` and `src/router.js`). Product
rule: a save that has started always finishes, even if the seller switches tab while it is running.

- `app.js`, `src/`: the page and its WebMCP tools. This is the team's code.
  - `src/state.js` the page's state; `src/ui.js` the view and tabs; `src/router.js` switching tabs; `src/scope.js` a
    tab's lifetime; `src/editor.js` the Edit tab and its tools; `src/preview.js` the Preview tab and its tools;
    `src/draft.js` unsaved drafts.
- `api.js`: the marketplace's listing server, simulated in the page. Not ours: don't change it.
- `latency.js`, `webmcp-host.js`: simulated network time and the WebMCP host. Don't change them.

Run it with any static file server from this folder, e.g. `python3 -m http.server 8000`, then open
http://127.0.0.1:8000/. `window.__app.getState()` returns the observable state.
