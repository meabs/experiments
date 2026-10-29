A bug report came in for this page:

> Some sellers' listings were left with the new title but the old description.

Find the cause and fix it. The page's code is `app.js` and `src/`. Don't change `api.js`, `latency.js` or
`webmcp-host.js`: they stand in for the server, the network and the browser.
