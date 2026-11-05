# SUPPORTORDERS: Shopizer's own defects behind the ticket (at 6a4a0a6)

Found by probing the unchanged code through the API before the ticket was written; nothing is planted.

1. **An order whose customer was deleted can't be opened.** `OrderFacadeImpl.getReadableOrder` checks the customer
   for null, but `customerFacade.getCustomerById` throws `ResourceNotFoundException` instead, so the order gives 404
   (probe: "No Customer found for ID").
2. **A customer's orders can only be listed while the account exists.** `GET /private/orders/customers/{id}` returns
   404 before looking at orders when the customer is gone.
3. **That list never reports its count.** The private `getReadableOrderList` sets `recordsTotal` on one object and
   returns another (`populateOrderList`), and returns null when there are no orders (as in CUSTOMERCART).
4. **The order list's page count is wrong.** `RepositoryHelper.paginateQuery` computes `count / size + 1` pages, one
   too many whenever the count divides evenly.
5. **A page after the last loses the totals.** The admin list facade sets `recordsTotal` to 0 whenever a page has no
   orders. With pages of one order, pages after the first came back empty in the probe.

Three hidden tests (the first page, later pages of a five-order list, paging with the status filter) pass on the
unchanged code: they guard behaviour the change must keep.
