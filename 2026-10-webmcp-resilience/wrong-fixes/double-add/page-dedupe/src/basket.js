import * as api from '../api.js';
import { state, update } from './state.js';
import { withRetry } from './net.js';
import { track } from './analytics.js';

const newKey = () => crypto.randomUUID();

export async function refreshBasket() {
  update({ basket: await withRetry(() => api.getBasket()) });
  return state.basket;
}

// Adds a product to the basket. Used by the Add buttons and by the assistant's add_to_cart tool. Every request carries
// an idempotency key, so the server never applies the same request twice.
const seen = new Map();
export function addToCart(input) {
  const { requestId } = input;
  if (requestId == null) return addNow(input);
  if (!seen.has(requestId)) seen.set(requestId, addNow(input));
  return seen.get(requestId);
}
async function addNow({ sku, quantity = 1, requestId, source = 'page' }) {
  if (!Number.isInteger(quantity) || quantity < 1) throw new Error('quantity must be a positive integer');
  track('add_to_cart', { sku, quantity, source, requestId });
  const result = await withRetry(() => api.addItem(sku, quantity, { idempotencyKey: newKey() }));
  if (result.code !== 'OK') return result;
  const name = state.products.find((p) => p.sku === sku)?.name ?? sku;
  update({ message: source === 'assistant' ? `The assistant added ${name}` : `Added ${name}` });
  await refreshBasket();
  return { code: 'OK', sku, quantityInBasket: result.quantity };
}

export async function removeFromCart(sku) {
  track('remove_from_cart', { sku });
  const result = await api.removeLine(sku);
  await refreshBasket();
  return result;
}
