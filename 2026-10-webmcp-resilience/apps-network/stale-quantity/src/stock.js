import * as api from '../api.js';
import { view, patch } from './state.js';

// Warns when the basket asks for more than the warehouse has.
export async function checkStock() {
  const { available } = await api.getStock(view.sku);
  patch({ available });
}

export function stockNote(v) {
  if (v.available == null) return '';
  if (v.quantity > v.available) return `Only ${v.available} left: we will send what we have.`;
  return v.available < 10 ? `Only ${v.available} left.` : 'In stock.';
}
