Last night someone deleted our store's super administrator account (admin@shopizer.com, user id 1) through the admin REST API, and nobody could log in to the back office until we restored the database. The code looks as if it already prevents that, but it does not.

Deleting the super administrator with DELETE /api/v1/private/user/{id} must be refused with HTTP 400 Bad Request, and the account must keep working. Deleting a user id that does not exist must answer 404 Not Found. Deleting any other user must keep working as it does today.
