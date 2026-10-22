When a shopper tries to register (POST /api/v1/customer/register) with an email address that already has an account, the API answers HTTP 500 Internal Server Error. The admin endpoint for creating customers (POST /api/v1/private/customer) does the same.

Both must answer 409 Conflict when the email address is already used by a customer of the store, and must not create a second customer. Registering or creating a customer with a new email address must keep working as before.
