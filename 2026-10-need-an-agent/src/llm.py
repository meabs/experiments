"""A minimal OpenRouter chat client: one place for the model, retries on transport errors, and usage accounting.

The key is read from ~/.config/openrouter.key and never printed. Transport failures (network, 429, 5xx from
OpenRouter or the provider) are retried with backoff, up to 5 times; they are infrastructure noise, not part of the
experiment, and are counted separately (LLM.transport_retries). The shop's injected faults are a different thing:
they come back from the shop's tools, never from here.
"""
import json, os, time, urllib.error, urllib.request

URL = "https://openrouter.ai/api/v1/chat/completions"


class LLM:
    def __init__(self, model):
        self.model = model
        self.key = open(os.path.expanduser("~/.config/openrouter.key")).read().strip()
        self.calls = []            # one record per model call: tokens, cost, seconds
        self.transport_retries = 0

    def chat(self, messages, tools=None, json_mode=False):
        body = {"model": self.model, "messages": messages, "usage": {"include": True}}
        if tools:
            body["tools"] = tools
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        data = json.dumps(body).encode()
        for attempt in range(6):
            t = time.time()
            try:
                req = urllib.request.Request(URL, data, {"Authorization": f"Bearer {self.key}",
                                                         "Content-Type": "application/json"})
                r = json.load(urllib.request.urlopen(req, timeout=180))
                if "choices" not in r or not r["choices"]:
                    raise RuntimeError(f"no choices: {str(r)[:200]}")
                break
            except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError, ConnectionError) as e:
                code = getattr(e, "code", None)
                if code in (400, 401, 402, 403) or attempt == 5:
                    raise
                self.transport_retries += 1
                time.sleep(2 * (attempt + 1))
        u = r.get("usage") or {}
        self.calls.append({"seconds": round(time.time() - t, 2), "prompt": u.get("prompt_tokens", 0),
                           "completion": u.get("completion_tokens", 0),
                           "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
                           "cost": u.get("cost", 0.0), "provider": r.get("provider")})
        return r["choices"][0]["message"]

    def usage(self):
        return {"llm_calls": len(self.calls), "prompt_tokens": sum(c["prompt"] for c in self.calls),
                "completion_tokens": sum(c["completion"] for c in self.calls),
                "reasoning_tokens": sum(c["reasoning"] for c in self.calls),
                "cost": round(sum(c["cost"] for c in self.calls), 6),
                "llm_seconds": round(sum(c["seconds"] for c in self.calls), 2),
                "transport_retries": self.transport_retries}


def parse_json(text):
    """The JSON object in a model's reply (tolerates code fences and text around it); None if there isn't one."""
    if not text:
        return None
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e < s:
        return None
    try:
        return json.loads(text[s:e + 1])
    except json.JSONDecodeError:
        return None
