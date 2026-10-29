A bug report came in for this page:

> Customers say a change to their email address or phone number sometimes goes back to the old value.

Find the cause and fix it. The page's code is `app.js` and `src/`. Don't change `api.js`, `latency.js` or
`webmcp-host.js`: they stand in for the server, the network and the browser.
