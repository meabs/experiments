# CATEGORYDELETE: Shopizer's own defects behind the ticket (at 6a4a0a6)

Found by probing the unchanged code through the API before the ticket was written; nothing is planted.

1. **Deleting a category deletes products.** `CategoryServiceImpl.delete` deletes every product whose only category
   it was (and, through a stale check, can delete others), which then breaks carts and orders holding them as in
   PRODUCTDELETE (probe: the product is gone after its category is deleted).
2. **A product's other categories are wiped.** The products come from a query that joins only the deleted
   categories; saving that partly loaded collection removes the product's other categories too (Shopizer's own
   comment there notes the session needs refreshing).
3. **Categories below are never found.** The descendant lookup appends the category's id to a lineage that already
   ends with it (`/1/` becomes `/1/1/`), so subcategories are left behind.
4. **No category can be read by id.** `CategoryApi` maps `/category/{id}` and `/category/{friendlyUrl}` to the same
   path; Spring rejects every such request as ambiguous (HTTP 500), deleted or not.
5. **A missing category is a 500, not a 404.** `CategoryFacadeImpl.getOne` uses `getById(id)`, which returns a lazy
   proxy rather than null, and fails later.
