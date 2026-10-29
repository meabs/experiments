import { view, patch, subscribe } from './state.js';
import { setQuantity } from './quantity.js';
import { stockNote } from './stock.js';
import { estimate } from './delivery.js';

const $ = (id) => document.getElementById(id);

function render(v) {
  $('name').textContent = v.name;
  $('quantity').textContent = String(v.quantity);
  $('line-total').textContent = v.price ? `£${(v.price * v.quantity).toFixed(2)}` : '';
  $('stock').textContent = stockNote(v);
  $('eta').textContent = v.eta;
  $('message').textContent = v.message;
}

const fail = (e) => patch({ message: e.message });

export function bindControls() {
  subscribe(render);
  $('plus').addEventListener('click', () => {
    if (view.quantity < 99) setQuantity(view.quantity + 1).catch(fail);
  });
  $('minus').addEventListener('click', () => {
    if (view.quantity > 1) setQuantity(view.quantity - 1).catch(fail);
  });
  $('estimate').addEventListener('click', () => { estimate($('postcode').value).catch(fail); });
}
