import * as api from '../api.js';
import { get, set } from './state.js';
import { abortable, isAbort } from './abortable.js';
import { followOrder } from './order-status.js';

// Places the order: price the basket, take payment, create the order. Used by the Place order button and by the
// assistant's place_order tool; the assistant may cancel a call it no longer needs (signal). If the checkout is
// cancelled or fails after the customer has paid, the payment is refunded.
export async function placeOrder({ signal } = {}) {
  let payment = null;
  set({ placing: true, message: 'Placing order…' });
  try {
    const quote = await abortable(api.getQuote(), signal);
    payment = await abortable(api.charge(quote.total), signal);
    const order = await abortable(api.createOrder(payment.id), signal);
    set({ message: `Order ${order.id} placed`, order: { id: order.id, status: order.status } });
    followOrder(order.id);
    return { code: 'OK', orderId: order.id, total: quote.total };
  } catch (e) {
    if (payment) await api.refund(payment.id);
    if (isAbort(e)) {
      set({ message: 'Order cancelled' });
      return { code: 'CANCELLED' };
    }
    set({ message: `Could not place the order: ${e.message}` });
    throw e;
  } finally {
    set({ placing: false });
  }
}

export const isPlacing = () => get().placing;
