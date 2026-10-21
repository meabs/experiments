Our back-office app shows "server error" for ordinary mistakes when managing admin users through the REST API, so our admins think the system is broken.

- Creating a user (POST /api/v1/private/user/) with a user name that already exists answers 500. It must answer 409 Conflict.
- Updating a user (PUT /api/v1/private/user/{id}) or changing the password of a user (PATCH /api/v1/private/user/{id}/password) whose id does not exist answers 500. It must answer 404 Not Found.
- Changing a password with the wrong current password answers 500. It must answer 400 Bad Request, and the password must stay as it was.

Everything that works today must keep working, including changing a password with the right current password and the 404 answers that other user endpoints already give.
