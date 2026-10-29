import { subscribe, set } from './state.js';
import { placeOrder, isPlacing } from './checkout.js';
import { chooseDelivery } from './quote.js';

const $ = (id) => document.getElementById(id);

function render(s) {
  $('lines').replaceChildren(...s.lines.map((l) => {
    const li = document.createElement('li');
    li.textContent = `${l.quantity} × ${l.name}`;
    return li;
  }));
  const select = $('address');
  if (select.options.length !== s.addresses.length) select.replaceChildren(...s.addresses.map((a) => new Option(a.label, a.id)));
  select.value = s.delivery;
  $('total').textContent = `Total: £${s.total.toFixed(2)}`;
  $('place').disabled = s.placing;
  $('message').textContent = s.message;
  $('order-status').textContent = s.order ? `Order ${s.order.id}: ${s.order.status}` : '';
}

export function bindControls() {
  subscribe(render);
  $('place').addEventListener('click', () => {
    if (isPlacing()) return;
    placeOrder().catch(() => {});
  });
  $('address').addEventListener('change', (e) => {
    chooseDelivery(e.target.value).catch((err) => set({ message: err.message }));
  });
}
