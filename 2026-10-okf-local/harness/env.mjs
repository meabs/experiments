// the browser globals the storefront reads
globalThis.window = globalThis;
globalThis._env_ = { APP_BASE_URL: "http://backend.invalid", APP_API_VERSION: "/api/v1/", APP_MERCHANT: "DEFAULT" };
const store = {};
globalThis.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } };
