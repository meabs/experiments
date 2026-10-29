// The page's state. patch() merges a change and re-renders.
const subscribers = [];
export const view = { sku: 'tea-02', name: '', price: 0, quantity: 0, available: null, eta: '', message: '' };

export function patch(change) {
  Object.assign(view, change);
  for (const fn of subscribers) fn(view);
}

export const subscribe = (fn) => subscribers.push(fn);
