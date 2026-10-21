When one of our administrators edits a colleague's back-office account through the admin REST API (PUT /api/v1/private/user/{id}), for example to fix a typo in their name, the colleague's account is disabled and they can no longer work until someone re-enables it.

Editing a user's details must not change whether the account is enabled: an enabled user stays enabled, and a disabled user stays disabled.
