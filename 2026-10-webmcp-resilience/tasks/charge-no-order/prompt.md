A bug report came in for this page:

> A few customers were charged but never got an order. Support also found an order whose payment had been refunded.

Find the cause and fix it. The page's code is `app.js` and `src/`. Don't change `api.js`, `latency.js` or
`webmcp-host.js`: they stand in for the server, the network and the browser.
