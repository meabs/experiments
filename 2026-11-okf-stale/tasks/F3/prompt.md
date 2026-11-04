Ticket: show what's left of today's limit.

Customers keep hitting their daily payment limit without knowing it. The app wants to show, before they pay, how much
they can still pay out today; support staff and admins want the same figure in the back office.

Add `GET /api/accounts/{accountId}/payment-allowance`. It returns `{"dailyLimit", "paidToday", "remaining"}` for the
account, where `paidToday` is what counts towards today's limit and `remaining` is what the customer can still pay
today (never below 0). It must agree with the limit check payments already make.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
