The admin customer list, GET /api/v1/private/customers?page=P&count=N, does not page properly. Later pages repeat customers from earlier pages or return more than N customers, "recordsTotal" is always 0, and "totalPages" is wrong.

Make the list page correctly. page is zero-based, and each page holds at most count customers. Going through every page must return each customer exactly once, and a page past the end returns no customers. recordsTotal must be the total number of customers in the store, and totalPages the number of pages of that size.
