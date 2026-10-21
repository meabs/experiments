Category codes must be unique within a store. When an admin creates a category with a code that another category already uses (POST /api/v1/private/category), or changes a category's code to one already in use (PUT /api/v1/private/category/{id}), the API answers 500 Internal Server Error, with a raw database error in the message.

Both cases must answer 409 Conflict and store nothing. Updating a category while keeping its own code must keep working.
