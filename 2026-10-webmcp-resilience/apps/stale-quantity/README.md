# Basket

The basket page of an online tea shop: one line with **−** and **+** buttons, stock and a delivery-time check. The
shop's AI assistant can change the quantity through WebMCP tools (`set_quantity` and others, registered in
`src/tools.js`).

- `app.js`, `src/`: the page and its WebMCP tools. This is the team's code.
  - `src/state.js` the page's state; `src/ui.js` the view and buttons; `src/quantity.js` changing the quantity;
    `src/stock.js` stock warnings; `src/delivery.js` delivery estimates; `src/tools.js` the assistant's tools.
- `api.js`: the shop's cart server, simulated in the page. Not ours: don't change it.
- `latency.js`, `webmcp-host.js`: simulated network time and the WebMCP host. Don't change them.

Run it with any static file server from this folder, e.g. `python3 -m http.server 8000`, then open
http://127.0.0.1:8000/. `window.__app.getState()` returns the observable state.
