# shopapi

The Hartley & Finch shop API: accounts, orders, refunds, gift cards, reviews, product images and payment webhooks,
plus a small admin area for the customer-service team. Flask and SQLite.

## Running locally

```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/seed.py          # creates shop.db with demo data
python run.py                   # http://127.0.0.1:5000
pytest
```

Demo accounts (password `demo-password-1` for all): `priya.shah@mail.test`, `tom.okafor@mail.test`, and the staff
account `admin@hartleyfinch.co.uk`.

## Layout

- `shopapi/__init__.py`: app factory, request hooks
- `shopapi/auth.py`: accounts, login, tokens, password reset
- `shopapi/orders.py`: orders, cancellations, refunds
- `shopapi/products.py`: catalogue, search, reviews, product pages
- `shopapi/basket.py`, `shopapi/giftcards.py`, `shopapi/images.py`, `shopapi/payments.py`, `shopapi/admin.py`
- `packages/hf_payments`: our payment-provider client (published to the internal index; installed editable for dev)

## Deploying

Production installs `requirements.txt` on the app servers; config comes from `config.py`.
