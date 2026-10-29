import * as api from '../api.js';
import { view, patch } from './state.js';
import { checkStock } from './stock.js';

// The newest change sent from each source (the buttons, or the assistant). A response to an older change from the same
// source is out of date by the time it arrives, so it is not shown.
const latest = { all: 0 };

// Changes the line's quantity. Used by the − and + buttons and by the assistant's set_quantity tool.
export async function setQuantity(quantity, source = 'page') {
  if (!Number.isInteger(quantity) || quantity < 1 || quantity > 99) throw new Error('quantity must be 1 to 99');
  const token = ++latest.all;
  patch({ quantity, message: '' }); // show the change at once
  const result = await api.setQuantity(view.sku, quantity);
  if (result.code !== 'OK') return result;
  if (token !== latest.all) return { code: 'OK', sku: view.sku, quantity: result.quantity, superseded: true };
  patch({ quantity: result.quantity, message: 'Basket updated' });
  void checkStock();
  return { code: 'OK', sku: view.sku, quantity: result.quantity };
}

export async function loadLine() {
  const line = await api.getLine(view.sku);
  patch({ name: line.name, price: line.price, quantity: line.quantity });
  return line;
}
