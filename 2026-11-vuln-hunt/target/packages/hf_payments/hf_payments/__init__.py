"""Client for the payment provider's REST API."""
import requests

DEFAULT_TIMEOUT = 5


class PaymentError(Exception):
    pass


class Client:
    def __init__(self, base_url, api_key, timeout=DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get(self, path):
        r = requests.get(f"{self.base_url}{path}", headers={"Authorization": f"Bearer {self.api_key}"},
                         timeout=self.timeout)
        if r.status_code >= 400:
            raise PaymentError(f"{r.status_code} from payment provider")
        return r.json()

    def payment_status(self, payment_id):
        """Returns "paid", "pending" or "failed"."""
        return self._get(f"/v1/payments/{payment_id}")["status"]

    def refund(self, payment_id, amount_pence):
        r = requests.post(f"{self.base_url}/v1/payments/{payment_id}/refunds", json={"amount": amount_pence},
                          headers={"Authorization": f"Bearer {self.api_key}"}, timeout=self.timeout)
        if r.status_code >= 400:
            raise PaymentError(f"{r.status_code} from payment provider")
        return r.json()["refund_id"]
