"""Synthetic caller of Requests for an interview-skill test; not production code."""

import requests


class BatchClient:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers["Authorization"] = f"Bearer {token}"

    def submit(self, batch):
        try:
            response = self.session.post(
                f"{self.base_url}/batches",
                json=batch,
                allow_redirects=False,
                timeout=(3, 20),
            )
        except requests.Timeout:
            return {"state": "unknown"}
        if response.is_redirect:
            return {"state": "endpoint_changed"}
        response.raise_for_status()
        return {"state": "accepted", "receipt": response.json()}
