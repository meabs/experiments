Our support team needs to find customers in the admin customer list, GET /api/v1/private/customers. Add three optional filters to it:

- email: customers whose email address contains the given text.
- name: customers whose billing first name or billing last name contains the given text.
- country: customers whose billing country is the given country code (for example CA).

Text matching ignores upper and lower case. Filters can be combined, and a customer must then match every filter given. Without filters, the list behaves as it does now.
