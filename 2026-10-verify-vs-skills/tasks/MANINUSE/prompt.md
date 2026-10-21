When a merchant deletes a manufacturer that some products still use (DELETE /api/v1/private/manufacturer/{id}), the API answers 503 Service Unavailable, so the admin app shows "server down, try again later". Retrying never helps.

A manufacturer that is still used by at least one product must not be deleted, and the API must answer 409 Conflict. Deleting a manufacturer that no product uses keeps working, and deleting an id that does not exist keeps answering 404.
