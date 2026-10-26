Part 1 – stock-alert domain and core service

Own these files (and any new files in the same core/model packages): sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/; sm-core/src/main/java/com/salesmanager/core/business/repositories/; sm-core/src/main/java/com/salesmanager/core/business/services/; and persistence/configuration files needed for the alert/outbox domain. Do not edit sm-shop API/facade files owned by Part 2 or inventory facade/API files owned by Part 3.

Implement the alert and outbox entities, repositories, and a service API that Part 2 can call. Expose clear methods for creating/cancelling/listing alerts and for processing pending alerts when a product transitions from zero stock to positive stock (including product name for outbox subject). Ensure store scoping, case-insensitive email matching, duplicate-pending idempotency, timestamps/statuses, and cascade/orphan cleanup when a product is deleted. Part 3 will invoke the transition method from inventory update.

Requirements from TASK.md applying here:

- “Sending means recording the message in a store outbox that admins can read; no real email is sent.”
- “An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.”
- “Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.”
- “When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, \"sentAt\" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.”
- “After a product sells out again, the same email can ask again, which makes a new pending alert.”
- “A product with alerts can still be deleted as before, and its alerts go with it.”

Part 2 relies on service methods/classes you provide (name them consistently and document via signatures), returning alert/outbox domain objects with id, sku, email, status, createdAt, sentAt and outbox to/sku/subject/createdAt. Part 3 relies on a method accepting product/store and old/new quantities, sending only on 0 -> >0.
