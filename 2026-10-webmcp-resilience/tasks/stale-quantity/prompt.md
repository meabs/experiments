A bug report came in for this page:

> The basket sometimes ends up with a different quantity from the one the customer chose last.

Find the cause and fix it. The page's code is `app.js` and `src/`. Don't change `api.js`, `latency.js` or
`webmcp-host.js`: they stand in for the server, the network and the browser.
