import * as api from '../api.js';
import { setState } from './state.js';

export async function loadPreferences() {
  setState({ preferences: await api.getPreferences() });
}

export async function setPreference(key, value) {
  const r = await api.setPreference(key, value);
  if (r.code === 'OK') setState({ preferences: r.preferences, message: 'Preferences saved' });
  return r;
}
