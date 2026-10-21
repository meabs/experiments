Our support team needs a working customer search in the admin API. GET /api/v1/private/customers should take these optional filters:

- email: the email address contains the given text.
- name: the billing first name or the billing last name contains the given text.
- country: the billing country is the given country code (for example CA).

Text matching ignores case, and when several filters are given, a customer must match all of them.

Results come in pages: page (zero-based) and count (customers per page). Going through the pages must return every matching customer exactly once, a page past the end is empty, "recordsTotal" is the number of matching customers, and "totalPages" is the number of pages. Today paging repeats customers and the totals are wrong, so check those too.
