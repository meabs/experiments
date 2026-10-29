// Simulated network and server time for api.js. Each backend call waits before it is handled. Tests can set
// window.__apiLatency = { callName: ms } or { callName: [ms, ms, ...] } (one value per call, in order) before the page
// loads. Do not change this file: it is part of the simulated backend.
const DEFAULT_MS = 120;

export function wait(name) {
  const l = window.__apiLatency?.[name];
  const ms = Array.isArray(l) ? (l.length ? l.shift() : DEFAULT_MS) : (l ?? DEFAULT_MS);
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Initial backend data can be overridden by tests with window.__apiSeed before the page loads.
export function seed(defaults) {
  return structuredClone({ ...defaults, ...(window.__apiSeed ?? {}) });
}
