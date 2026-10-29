import * as api from '../api.js';
import { view, patch } from './state.js';
import { checkStock } from './stock.js';

// Every change the page sends, from the buttons or the assistant, gets the next number. The server ignores a change
// older than one it has already applied (STALE), and the page only shows the answer to the newest change.
let sequence = 0;

// Changes the line's quantity. Used by the − and + buttons and by the assistant's set_quantity tool.
export async function setQuantity(quantity, source = 'page') {
  if (!Number.isInteger(quantity) || quantity < 1 || quantity > 99) throw new Error('quantity must be 1 to 99');
  const mine = ++sequence;
  patch({ quantity, message: '' }); // show the change at once
  const result = await api.setQuantity(view.sku, quantity, { sequence: mine });
  if (result.code === 'STALE') return { code: 'OK', sku: view.sku, quantity: result.quantity, superseded: true };
  if (result.code !== 'OK') return result;
  if (mine !== sequence) return { code: 'OK', sku: view.sku, quantity: result.quantity, superseded: true };
  patch({ quantity: result.quantity, message: 'Basket updated' });
  void checkStock();
  return { code: 'OK', sku: view.sku, quantity: result.quantity };
}

export async function loadLine() {
  const line = await api.getLine(view.sku);
  patch({ name: line.name, price: line.price, quantity: line.quantity });
  return line;
}
