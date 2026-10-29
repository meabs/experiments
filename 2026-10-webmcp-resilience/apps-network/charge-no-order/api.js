// Simulated backend for checkout. It stands in for the shop's order and payment servers, which this team does not own:
// do not change this file. Every call takes time (see latency.js). Once a call has been sent it runs to the end on the
// server, whether or not the page is still waiting for the answer.
import { wait, seed } from './latency.js';

const db = seed({
  basket: [{ sku: 'mug-01', name: 'Blue mug', quantity: 2, price: 8.5 }],
  addresses: [{ id: 'home', label: 'Home: 4 Elm Road, Leeds' }, { id: 'work', label: 'Work: 10 Park Square, Leeds' }],
  delivery: 'home',
  charges: [],
  orders: [],
});
let nextId = 1;

// The basket and its total, as the server prices it.
export async function getQuote() {
  await wait('getQuote');
  const total = db.basket.reduce((s, l) => s + l.quantity * l.price, 0) + (db.delivery === 'work' ? 0 : 3.95);
  return { lines: db.basket.map((l) => ({ ...l })), delivery: db.delivery, total };
}

export async function getAddresses() {
  await wait('getAddresses');
  return { addresses: db.addresses.map((a) => ({ ...a })), selected: db.delivery };
}

export async function setDelivery(addressId) {
  await wait('setDelivery');
  if (!db.addresses.some((a) => a.id === addressId)) return { code: 'UNKNOWN_ADDRESS' };
  db.delivery = addressId;
  return { code: 'OK' };
}

// Takes payment from the customer's saved card.
export async function charge(amount) {
  await wait('charge');
  const c = { id: `ch${nextId++}`, amount, refunded: false };
  db.charges.push(c);
  return { ...c };
}

// Gives a charge back in full.
export async function refund(chargeId) {
  await wait('refund');
  const c = db.charges.find((x) => x.id === chargeId);
  if (!c) return { code: 'UNKNOWN_CHARGE' };
  c.refunded = true;
  return { code: 'OK' };
}

// Creates the order for a charge.
export async function createOrder(chargeId) {
  await wait('createOrder');
  const o = { id: `o${nextId++}`, chargeId, status: 'received' };
  db.orders.push(o);
  return { ...o };
}

export async function getOrder(orderId) {
  await wait('getOrder');
  const o = db.orders.find((x) => x.id === orderId);
  return o ? { ...o } : { code: 'UNKNOWN_ORDER' };
}

// Server-side view, for tests and support staff: charges not refunded, refunds, orders.
window.__backend = {
  snapshot: () => ({
    charges: db.charges.filter((c) => !c.refunded).length,
    refunds: db.charges.filter((c) => c.refunded).length,
    orders: db.orders.length,
  }),
};
