A bug report came in for this page:

> Some customers find two of an item in their basket when they only added one. It seems to happen when the shop is busy.

Find the cause and fix it. The page's code is `app.js` and `src/`. Don't change `api.js`, `latency.js` or
`webmcp-host.js`: they stand in for the server, the network and the browser.
