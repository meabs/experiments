A bug report came in for this page:

> The Saturday spin class has ended up with more people booked than it has seats, twice in the last month.

Find the cause and fix it. The page's code is `app.js` and `src/`. Don't change `api.js`, `latency.js` or
`webmcp-host.js`: they stand in for the server, the network and the browser.
