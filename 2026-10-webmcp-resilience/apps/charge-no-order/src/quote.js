import * as api from '../api.js';
import { set } from './state.js';

export async function refreshQuote() {
  const quote = await api.getQuote();
  set({ lines: quote.lines, total: quote.total, delivery: quote.delivery });
  return quote;
}

export async function loadAddresses() {
  const { addresses, selected } = await api.getAddresses();
  set({ addresses, delivery: selected });
}

export async function chooseDelivery(addressId) {
  const r = await api.setDelivery(addressId);
  if (r.code === 'OK') await refreshQuote();
  return r;
}
