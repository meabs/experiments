The admin tax rate list, GET /api/v1/private/tax/rates, accepts page and count parameters but ignores them: it always returns every tax rate, in no particular order.

Make it page properly. page is zero-based, each page holds at most count rates, rates are sorted by code, and a page past the end returns no rates. "recordsTotal" must be the total number of tax rates in the store, "totalPages" the number of pages of that size, and "number" the number of rates on the returned page.
