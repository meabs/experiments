import { state, onChange } from './state.js';
import { addToCart, removeFromCart } from './basket.js';
import { applyPromo } from './promo.js';

const $ = (id) => document.getElementById(id);
const money = (n) => `£${n.toFixed(2)}`;

function button(label, onClick, attrs = {}) {
  const b = document.createElement('button');
  b.textContent = label;
  Object.assign(b, attrs);
  b.addEventListener('click', onClick);
  return b;
}

function row(text, ...children) {
  const li = document.createElement('li');
  li.append(text, ...children.flatMap((c) => [' ', c]));
  return li;
}

function render() {
  $('lines').replaceChildren(...state.basket.lines.map((l) =>
    row(`${l.quantity} × ${l.name}`, button('Remove', () => { void removeFromCart(l.sku); }))));
  const { subtotal, discount } = state.basket;
  $('totals').textContent = discount ? `${money(subtotal)} − ${money(discount)} = ${money(subtotal - discount)}`
    : `Total ${money(subtotal)}`;
  $('message').textContent = state.message;
}

export function renderProducts() {
  $('products').replaceChildren(...state.products.map((p) => row(`${p.name}, ${money(p.price)}`,
    button('Add', () => {
      addToCart({ sku: p.sku }).catch((e) => { state.message = e.message; render(); });
    }, { id: `add-${p.sku.split('-')[0]}` }))));
}

export function bindControls() {
  onChange(render);
  $('apply-promo').addEventListener('click', () => { void applyPromo($('promo').value); });
}
