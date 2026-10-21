A merchant reports: "When I create a product through the admin REST API (POST /api/v1/private/product) with "available": false, because it is not ready to sell yet, the product still comes back as available: GET /api/v2/product/{sku} shows "available": true."

Make the availability we send when creating a product be the availability that is stored and returned.
