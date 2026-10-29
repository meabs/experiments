# Checkout

The shop's checkout page: the basket, a delivery address and a **Place order** button. The shop's AI assistant can
also place the order through WebMCP tools (`place_order` and others, registered in `src/tools.js`).

- `app.js`, `src/`: the page and its WebMCP tools. This is the team's code.
  - `src/state.js` the page's state; `src/ui.js` the view and buttons; `src/quote.js` basket total and delivery;
    `src/checkout.js` placing the order; `src/abortable.js` cancelling waits; `src/order-status.js` following an order;
    `src/tools.js` the assistant's tools.
- `api.js`: the shop's order and payment servers, simulated in the page. Not ours: don't change it.
- `latency.js`, `webmcp-host.js`: simulated network time and the WebMCP host. Don't change them.

Run it with any static file server from this folder, e.g. `python3 -m http.server 8000`, then open
http://127.0.0.1:8000/. `window.__app.getState()` returns the observable state.
