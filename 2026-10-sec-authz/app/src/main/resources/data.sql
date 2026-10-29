-- Deterministic fixtures. Two tenants (banks): acme and globex. Users log in through the identity service; their
-- tokens carry sub = the user id, tenant and roles (see src/test/java/.../support/TestUsers.java).
--   acme:   u-alice, u-bob, u-dana (customers); u-sam, u-sue (support); u-ana (support + approver);
--           u-ada (admin); u-al (admin + approver)
--   globex: u-carol (customer); u-gus (support); u-gil (admin); u-gwen (approver)

INSERT INTO customers (id, tenant_id, user_id, name, email, phone, address, risk_score) VALUES
 ('c-1', 'acme',   'u-alice', 'Alice Archer', 'alice@acme.test', '01632 960101', '1 Mill Lane, York', 12),
 ('c-2', 'acme',   'u-bob',   'Bob Brown',    'bob@acme.test',   '01632 960102', '2 Kiln Row, Hull', 55),
 ('c-5', 'acme',   'u-dana',  'Dana Dale',    'dana@acme.test',  '01632 960105', '5 Weir Road, Ripon', 3),
 ('c-3', 'globex', 'u-carol', 'Carol Archer', 'carol@globex.test', '01632 960203', '3 Quay Street, Leeds', 20);

INSERT INTO accounts (id, tenant_id, customer_id, nickname, type, balance, daily_limit, status) VALUES
 (1, 'acme',   'c-1', 'Everyday', 'CURRENT', 1200.00, 500, 'OPEN'),
 (2, 'acme',   'c-1', 'Rainy day', 'SAVINGS', 8000.00, 250, 'OPEN'),
 (3, 'acme',   'c-2', 'Main',     'CURRENT',  300.00, 500, 'OPEN'),
 (4, 'globex', 'c-3', 'Joint',    'CURRENT', 2500.00, 700, 'OPEN'),
 (5, 'acme',   'c-5', 'Old ISA',  'SAVINGS',    0.00,   0, 'CLOSED');
ALTER TABLE accounts ALTER COLUMN id RESTART WITH 100;

-- Support users only see the accounts they are assigned to.
INSERT INTO support_assignments (id, tenant_id, support_user_id, account_id) VALUES
 (1, 'acme', 'u-sam', 1), (2, 'acme', 'u-sam', 2), (3, 'acme', 'u-sue', 3), (4, 'acme', 'u-ana', 3),
 (5, 'globex', 'u-gus', 4);
ALTER TABLE support_assignments ALTER COLUMN id RESTART WITH 100;

INSERT INTO transactions (id, account_id, amount, description, booked_on) VALUES
 (1, 1, -42.10, 'Grocer', '2026-09-28'), (2, 1, 1850.00, 'Salary', '2026-09-30'), (3, 3, -12.00, 'Bus pass', '2026-09-29'),
 (4, 4, -300.00, 'Rent share', '2026-09-30');
ALTER TABLE transactions ALTER COLUMN id RESTART WITH 100;

INSERT INTO statements (id, account_id, period, opening_balance, closing_balance) VALUES
 (1, 1, '2026-07', 900.00, 1010.00), (2, 1, '2026-08', 1010.00, 1100.00), (3, 1, '2026-09', 1100.00, 1200.00),
 (4, 2, '2026-09', 7900.00, 8000.00), (5, 3, '2026-09', 410.00, 300.00), (6, 4, '2026-09', 2700.00, 2500.00);
ALTER TABLE statements ALTER COLUMN id RESTART WITH 100;

INSERT INTO account_notes (id, account_id, author, body, internal, created_at) VALUES
 (1, 1, 'u-sam', 'Welcome pack sent.', FALSE, '2026-08-01T09:00:00Z'),
 (2, 1, 'u-sam', 'Fraud alert on card ending 4417; identity verified by phone.', TRUE, '2026-09-12T14:30:00Z'),
 (3, 1, 'u-ada', 'New debit card posted.', FALSE, '2026-09-13T10:00:00Z'),
 (4, 2, 'u-sam', 'Customer asked about fixed-rate savings.', FALSE, '2026-09-20T11:00:00Z'),
 (5, 3, 'u-sue', 'Overdraft reminder sent.', FALSE, '2026-09-25T08:00:00Z'),
 (6, 3, 'u-sue', 'Possible financial hardship: offer a payment plan before any charges.', TRUE, '2026-09-26T16:00:00Z'),
 (7, 4, 'u-gus', 'Joint holder dispute: do not discuss balance with second holder.', TRUE, '2026-09-18T12:00:00Z');
ALTER TABLE account_notes ALTER COLUMN id RESTART WITH 100;

INSERT INTO support_cases (id, tenant_id, account_id, customer_id, subject, status, assignee_user_id, opened_at) VALUES
 ('k-1', 'acme',   1, 'c-1', 'Card not arrived',       'OPEN', 'u-sam', '2026-09-10T09:00:00Z'),
 ('k-2', 'acme',   1, 'c-1', 'Disputed card payment',  'OPEN', 'u-sue', '2026-09-14T09:00:00Z'),
 ('k-3', 'acme',   3, 'c-2', 'Change of address',      'OPEN', 'u-sue', '2026-09-22T09:00:00Z'),
 ('k-5', 'acme',   3, 'c-2', 'Statement copy request', 'OPEN', NULL,    '2026-09-27T09:00:00Z'),
 ('k-4', 'globex', 4, 'c-3', 'Second card request',    'OPEN', 'u-gus', '2026-09-16T09:00:00Z');

INSERT INTO case_comments (id, case_id, author, body, internal, created_at) VALUES
 (1, 'k-1', 'u-alice', 'My new card has not come.', FALSE, '2026-09-10T09:00:00Z'),
 (2, 'k-1', 'u-sam', 'Reissued; tracked delivery.', FALSE, '2026-09-11T09:00:00Z'),
 (3, 'k-2', 'u-sue', 'Merchant has a history of chargebacks; escalate to fraud team.', TRUE, '2026-09-14T10:00:00Z'),
 (4, 'k-3', 'u-sue', 'Proof of address received.', FALSE, '2026-09-23T09:00:00Z'),
 (5, 'k-4', 'u-gus', 'Check second holder consent first.', TRUE, '2026-09-16T10:00:00Z');
ALTER TABLE case_comments ALTER COLUMN id RESTART WITH 100;

INSERT INTO closure_requests (id, tenant_id, account_id, requested_by, status, decided_by, decided_at, requested_at) VALUES
 (1, 'acme',   2, 'u-alice', 'PENDING', NULL, NULL, '2026-10-01T09:00:00Z'),
 (2, 'acme',   3, 'u-al',    'PENDING', NULL, NULL, '2026-10-02T09:00:00Z'),
 (3, 'acme',   5, 'u-dana',  'APPROVED', 'u-ana', '2026-09-01T12:00:00Z', '2026-08-30T09:00:00Z'),
 (4, 'globex', 4, 'u-carol', 'PENDING', NULL, NULL, '2026-10-03T09:00:00Z');
ALTER TABLE closure_requests ALTER COLUMN id RESTART WITH 100;
