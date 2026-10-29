# Shop

A small online tea shop: a product list with **Add** buttons, the basket and a promo code box. The shop's AI assistant
adds and removes items through WebMCP tools (`add_to_cart` and others, registered in `src/tools.js`).

- `app.js`, `src/`: the page and its WebMCP tools. This is the team's code.
  - `src/state.js` the page's state; `src/ui.js` the view and buttons; `src/basket.js` basket changes;
    `src/promo.js` promo codes; `src/net.js` retries for slow server calls; `src/analytics.js` product analytics;
    `src/tools.js` the assistant's tools.
- `api.js`: the shop's cart server, simulated in the page. Not ours: don't change it. Like the real one, it keeps the
  basket when the page is reloaded.
- `latency.js`, `webmcp-host.js`: simulated network time and the WebMCP host. Don't change them.

Run it with any static file server from this folder, e.g. `python3 -m http.server 8000`, then open
http://127.0.0.1:8000/. `window.__app.getState()` returns the observable state.
