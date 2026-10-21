Looking up a single category through the public REST API is broken. GET /api/v1/category/{id} (for example /api/v1/category/12) returns HTTP 500 Internal Server Error, and so does looking a category up by its friendly URL, GET /api/v1/category/{friendlyUrl} (for example /api/v1/category/dining-chairs).

Make both lookups work: a numeric value is a category id, anything else is a friendly URL. An id or friendly URL that does not exist must return 404 Not Found.
