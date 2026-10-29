# Your details

The account page of an online shop: the customer's name, email and phone in a form with a **Save** button, and their
message preferences. The shop's AI assistant can change details through WebMCP tools (`update_profile` and others,
registered in `src/tools.js`).

- `app.js`, `src/`: the page and its WebMCP tools. This is the team's code.
  - `src/state.js` the page's state; `src/ui.js` the view and controls; `src/form.js` the details form;
    `src/profile.js` loading and saving details; `src/preferences.js` message preferences; `src/validate.js` checks;
    `src/tools.js` the assistant's tools.
- `api.js`: the shop's customer server, simulated in the page. Not ours: don't change it.
- `latency.js`, `webmcp-host.js`: simulated network time and the WebMCP host. Don't change them.

Run it with any static file server from this folder, e.g. `python3 -m http.server 8000`, then open
http://127.0.0.1:8000/. `window.__app.getState()` returns the observable state.
