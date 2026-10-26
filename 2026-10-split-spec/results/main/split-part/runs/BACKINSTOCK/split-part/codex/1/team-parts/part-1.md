Part 1 — stock-alert domain and service

Own these files (and only these areas):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/stockalert/** (new entity/status/outbox model classes)
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/stockalert/** (new repositories)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/stockalert/** (service interface/implementation)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java only where needed to cascade-delete alerts with a product

Implement the persistence and business service used by the API and inventory code. Provide clear methods (names may be adapted to existing conventions) for finding a product by SKU/store, creating/cancelling pending alerts case-insensitively, listing alerts/outbox oldest first with optional PENDING/SENT filter, and sending all pending alerts for a product when stock transitions from zero to positive. The send operation must set SENT/sentAt and create one outbox message per alert, with subject "<product name> is back in stock". Keep store isolation and cascade/delete alerts when a product is deleted.

Exact task requirements applying to this part:
- “Sending means recording the message in a store outbox that admins can read; no real email is sent.”
- “When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, "sentAt" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.”
- “Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.”
- “After a product sells out again, the same email can ask again, which makes a new pending alert.”
- “A product with alerts can still be deleted as before, and its alerts go with it.”

Other parts rely on a service exposing operations equivalent to create/find pending, cancel, list alerts, list outbox, and notifyRestocked(product/store), plus entity getters for id/sku/email/status/createdAt/sentAt and outbox to/sku/subject/createdAt.
