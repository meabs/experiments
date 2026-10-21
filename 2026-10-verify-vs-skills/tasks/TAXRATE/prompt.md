Our accountant entered a tax rate of 150 by mistake through the admin REST API and it was accepted, and so was a negative rate.

Tax rates must be between 0 and 100 inclusive. Creating or updating a tax rate through the private REST API with a rate outside that range, or with no rate at all, must be rejected with HTTP 400 Bad Request, and nothing may be stored or changed.
