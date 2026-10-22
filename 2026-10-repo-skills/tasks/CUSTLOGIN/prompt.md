Our support team updates customer accounts through the admin REST API (PUT /api/v1/private/customer/{id}), and two kinds of update lock customers out.

When support sets a new password for a customer, the customer can no longer log in at all, neither with the new password nor with the old one. When support changes a customer's email address, the customer still has to log in with the old address, and the new one is refused.

After an admin update, a customer must log in (POST /api/v1/customer/login) with the password and email address the update set, and the old ones must no longer work. Updates that change neither must leave the customer's login as it was, and customers who register themselves must keep being able to log in.
