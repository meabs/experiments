Our API client treats 404 as "this item does not exist" and retries anything in the 5xx range. Two storefront endpoints answer wrongly for items that do not exist:

- GET /api/v1/manufacturer/{id} for an id that does not exist (or was deleted) answers 503 Service Unavailable.
- GET /api/v2/product/{sku} for a sku that does not exist answers 400 Bad Request.

Both must answer 404 Not Found when the item does not exist, and must keep answering 200 with the item when it does.
