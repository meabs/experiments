import * as api from '../api.js';
import { update } from './state.js';
import { refreshBasket } from './basket.js';

export async function applyPromo(code) {
  const clean = String(code ?? '').trim().toUpperCase();
  if (!clean) return { code: 'INVALID_PROMO' };
  const result = await api.applyPromo(clean);
  update({ message: result.code === 'OK' ? `Promo ${clean} applied` : 'That code is not valid' });
  if (result.code === 'OK') await refreshBasket();
  return result;
}
