import * as api from '../api.js';
import { set } from './state.js';

// After an order is placed, check its status a few times so the customer sees it move on.
export function followOrder(orderId, { everyMs = 5000, times = 3 } = {}) {
  let left = times;
  const tick = async () => {
    const o = await api.getOrder(orderId);
    if (o.status) set({ order: { id: orderId, status: o.status } });
    if (--left > 0) setTimeout(tick, everyMs);
  };
  setTimeout(tick, everyMs);
}
