// The page's state. set() merges a change and re-renders.
let current = { lines: [], total: 0, addresses: [], delivery: 'home', placing: false, message: '', order: null };
const listeners = [];

export const get = () => current;

export function set(patch) {
  current = { ...current, ...patch };
  for (const fn of listeners) fn(current);
}

export const subscribe = (fn) => listeners.push(fn);
