# Class booking

The gym's booking page. Customers pick a class and book with the **Book** button, and the gym's AI assistant books
through WebMCP tools (`book_seat` and others, registered in `src/tools.js`).

- `app.js`, `src/`: the page and its WebMCP tools. This is the team's code.
  - `src/state.js` the page's state; `src/ui.js` the view and buttons; `src/classes.js` the timetable;
    `src/bookings.js` booking, cancelling and the waiting list; `src/tools.js` the assistant's tools; `src/log.js` a
    debug log.
- `api.js`: the gym's booking server, simulated in the page. Not ours: don't change it.
- `latency.js`, `webmcp-host.js`: simulated network time and the WebMCP host. Don't change them.

Run it with any static file server from this folder, e.g. `python3 -m http.server 8000`, then open
http://127.0.0.1:8000/. `window.__app.getState()` returns the observable state.
