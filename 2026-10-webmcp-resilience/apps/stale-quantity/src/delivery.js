import * as api from '../api.js';
import { patch } from './state.js';

let lastAsked = '';

export async function estimate(postcode) {
  const clean = postcode.trim().toUpperCase();
  lastAsked = clean;
  const r = await api.deliveryEstimate(clean);
  if (clean !== lastAsked) return r; // the customer asked about another postcode since
  patch({ eta: r.code === 'OK' ? `About ${r.days} working day${r.days > 1 ? 's' : ''}` : 'Please check the postcode' });
  return r;
}
