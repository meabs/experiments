// The page's state. Changes go through update(), which re-renders.
const listeners = new Set();

export const state = { products: [], basket: { lines: [], subtotal: 0, discount: 0 }, message: '' };

export function update(patch) {
  Object.assign(state, patch);
  for (const fn of listeners) fn(state);
}

export function onChange(fn) {
  listeners.add(fn);
}
