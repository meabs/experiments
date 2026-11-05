# REVIEWS: Shopizer's own defects behind the ticket (at 6a4a0a6)

Found by probing the unchanged code through the API before the ticket was written; nothing is planted.

1. **The public review list exposes the reviewer.** Each review carries the full `ReadableCustomer`: email, billing
   and delivery addresses (probe: the reviewer's email and street address in an unauthenticated response).
2. **Anyone can review in another customer's name.** The logged-in endpoint trusts the body's `customerId` and never
   compares it with the token's customer (probe: accepted with 201).
3. **Validation and duplicates come out as server errors.** A second review is refused with 500, a rating above 5
   with 503, and ratings of 0, negatives or fractions are accepted.
4. **Merchant edits and deletes can't run.** Both map `{reviewid}` but bind `@PathVariable reviewId`, so every call
   fails before its code runs; behind that, an edit builds a new review (and a new description row) instead of
   changing the stored one, and a missing review id is a lazy proxy that fails later instead of a 404.
5. **The rating drifts.** `ProductReviewServiceImpl` keeps a running average that counts an edit as a new review and
   is never recalculated on delete; the product view then rounds it to half stars (probe: 5, 5 and 4 show 4.5).

Two hidden tests (the average of two reviews, a product with no reviews) pass on the unchanged code: they guard
behaviour the change must keep.
