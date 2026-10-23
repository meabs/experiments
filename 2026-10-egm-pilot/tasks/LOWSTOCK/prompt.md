Merchants want to see which products are running low, so they can reorder in time. Add a low-stock report to the admin REST API.

GET /api/v1/private/products/low-stock?store={store code}&threshold={n}

- It is an admin endpoint, protected like the other /api/v1/private endpoints.
- A product's stock is the total quantity across all of its inventory entries (usually one, created with the product). A product with no inventory entries has a stock of 0.
- The report lists every product of the requested store whose stock is at or below the threshold. Products of other stores are never listed.
- threshold is optional and defaults to 5. A negative or non-numeric threshold is rejected with HTTP 400 Bad Request.
- The response is HTTP 200 with a JSON body: {"threshold": n, "totalCount": k, "items": [{"id": productId, "sku": "...", "stock": total}, ...]}. "threshold" is the threshold used, "totalCount" the number of matching products across all pages.
- Items are ordered by stock, lowest first, then by sku, A to Z.
- The report is paged with the query parameters page (0-based, default 0) and count (items per page, default 20).
