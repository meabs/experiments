Our marketplace lets customers rate each other after a sale, and moderators correct reviews when a dispute is settled. Correcting one does not work: PUT /api/v1/private/customers/{id}/reviews/{reviewId} answers with a server error.

An edit must change that review's rating and text. A review id that does not exist for that customer must answer 404 Not Found, both when editing and when deleting.
