// Simulated backend for the shop's basket. It stands in for the shop's cart server, which this team does not own: do
// not change this file. Every call takes time (see latency.js). Like the real server, it keeps the basket when the
// customer reloads the page (here, in sessionStorage).
import { wait, seed } from './latency.js';

const KEY = '__cartServer';
const saved = sessionStorage.getItem(KEY);
const db = saved ? JSON.parse(saved) : seed({
  lines: {},
  products: {
    'mug-01': { name: 'Blue mug', price: 8.5 },
    'tea-02': { name: 'Earl Grey, 250 g', price: 6 },
    'pot-03': { name: 'Teapot, 1 l', price: 24 },
  },
  promo: null,
  applied: {}, // idempotency key -> result
});
const persist = () => sessionStorage.setItem(KEY, JSON.stringify(db));
const running = new Map(); // idempotency key -> result promise, while the first call with that key is in progress

async function add(sku, quantity) {
  await wait('addItem');
  if (!db.products[sku]) return { code: 'UNKNOWN_SKU' };
  db.lines[sku] = (db.lines[sku] ?? 0) + quantity;
  persist();
  return { code: 'OK', sku, quantity: db.lines[sku] };
}

// Adds `quantity` of `sku` to the basket. With options.idempotencyKey, the server applies a given key once: a repeat
// with the same key (while the first is still running, or any time after) gets the first call's result back without
// adding again.
export function addItem(sku, quantity, options = {}) {
  const key = options.idempotencyKey;
  if (key == null) return add(sku, quantity);
  if (key in db.applied) return Promise.resolve({ ...db.applied[key] });
  if (!running.has(key)) {
    running.set(key, add(sku, quantity).then((r) => {
      db.applied[key] = r;
      persist();
      running.delete(key);
      return r;
    }));
  }
  return running.get(key).then((r) => ({ ...r }));
}

export async function removeLine(sku) {
  await wait('removeLine');
  delete db.lines[sku];
  persist();
  return { code: 'OK' };
}

export async function getBasket() {
  await wait('getBasket');
  const lines = Object.entries(db.lines).map(([sku, quantity]) => ({ sku, name: db.products[sku].name, quantity,
    price: db.products[sku].price }));
  const subtotal = lines.reduce((s, l) => s + l.quantity * l.price, 0);
  return { lines, subtotal, discount: db.promo ? +(subtotal * 0.1).toFixed(2) : 0, promo: db.promo };
}

export async function getProducts() {
  await wait('getProducts');
  return Object.entries(db.products).map(([sku, p]) => ({ sku, ...p }));
}

export async function applyPromo(code) {
  await wait('applyPromo');
  if (code !== 'TEA10') return { code: 'INVALID_PROMO' };
  db.promo = code;
  persist();
  return { code: 'OK' };
}

// Server-side view, for tests and support staff.
window.__backend = { snapshot: () => ({ lines: { ...db.lines } }) };
