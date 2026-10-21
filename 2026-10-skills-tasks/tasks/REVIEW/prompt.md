Product reviews (POST /api/v1/private/products/{id}/reviews, and PUT /api/v1/private/products/{id}/reviews/{reviewId} for edits) answer with the wrong status codes, and one bad case gets through:

- A rating of 0 or a negative rating is accepted and stored.
- A rating above 5 answers 503 Service Unavailable.
- A second review of the same product by the same customer answers 500 Internal Server Error.

Ratings must be between 1 and 5 inclusive. A rating outside that range must answer 400 Bad Request and store nothing, on both create and edit. A second review of the same product by the same customer must answer 409 Conflict and store nothing. Valid reviews keep answering 201 Created, as now.
