A customer complained that anyone can see her email address and home address next to the review she left on a product. Looking into it, support found more problems with product reviews: a customer who reviews a product a second time gets a server error, so does a rating of 9, and when a review is edited or removed by the merchant the product's star rating doesn't change.

Fix product reviews:

- The public list of a product's reviews (GET /api/v1/product/{id}/reviews) shows, for each review, its id, rating, description, date and the reviewer's first name only: no email address, no billing or delivery address, nothing else about the customer.
- A logged-in customer reviews a product with POST /api/v1/auth/products/{id}/reviews ({"rating": 4, "description": "...", "customerId": ..., "productId": ..., "language": "en"}). A rating must be a whole number from 1 to 5, otherwise HTTP 400 Bad Request. A customer can review a product once: a second review of the same product gives HTTP 409 Conflict. A review sent with another customer's id gives HTTP 403 Forbidden. Nothing is stored when a review is refused.
- Merchants can change a review's rating or description (PUT /api/v1/private/products/{id}/reviews/{reviewId}) and delete it (DELETE on the same path); a review that doesn't exist, or belongs to another product, gives HTTP 404 Not Found.
- A product's "rating" (the average of its reviews' ratings, to one decimal place, halves rounding up) and "ratingCount" (GET /api/v2/product/{sku}) are always right: after every review is added, changed or deleted. A product with no reviews shows 0 and 0.

When you have finished, reply with one short paragraph saying what you changed.
