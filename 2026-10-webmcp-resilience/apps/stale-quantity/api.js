// Simulated backend for the basket. It stands in for the shop's cart server, which this team does not own: do not
// change this file. Every call takes time (see latency.js), and calls can finish in a different order from the one
// they were sent in.
import { wait, seed } from './latency.js';

const db = seed({
  lines: { 'tea-02': 1 },
  products: { 'tea-02': { name: 'Earl Grey, 250 g', price: 6 } },
  stock: { 'tea-02': 40 },
});
const lastSequence = {};

// Sets the quantity of a basket line. The server applies a call when it arrives. With options.sequence (a number that
// grows with each change the page sends for that line), the server ignores a call older than one it has already
// applied and answers { code: 'STALE', quantity: <current> }.
export async function setQuantity(sku, quantity, options = {}) {
  await wait('setQuantity');
  if (!(sku in db.lines)) return { code: 'UNKNOWN_SKU' };
  const seq = options.sequence;
  if (seq != null) {
    if (lastSequence[sku] != null && seq <= lastSequence[sku]) return { code: 'STALE', sku, quantity: db.lines[sku] };
    lastSequence[sku] = seq;
  }
  db.lines[sku] = quantity;
  return { code: 'OK', sku, quantity };
}

export async function getLine(sku) {
  await wait('getLine');
  const p = db.products[sku];
  return { sku, name: p.name, price: p.price, quantity: db.lines[sku] };
}

export async function getStock(sku) {
  await wait('getStock');
  return { sku, available: db.stock[sku] ?? 0 };
}

export async function deliveryEstimate(postcode) {
  await wait('deliveryEstimate');
  if (!/^[A-Z]{1,2}\d/i.test(postcode)) return { code: 'BAD_POSTCODE' };
  return { code: 'OK', days: postcode.toUpperCase().startsWith('LS') ? 1 : 3 };
}

// Server-side view, for tests and support staff.
window.__backend = { snapshot: () => ({ lines: { ...db.lines } }) };
