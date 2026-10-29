import * as api from '../api.js';
import { state, setState } from './state.js';
import { FIELDS, problem } from './validate.js';

let form = null;
// The profile as the form last showed it. Save sends only the fields the customer has changed from this, so it never
// writes back an old value over a change the assistant made meanwhile.
let shown = {};

export function useForm(f) {
  form = f;
}

export async function loadProfile() {
  const profile = await api.getProfile();
  setState({ profile });
  form.fill(profile);
  shown = { ...profile };
}

// Saves the form. Used by the Save button.
export async function saveForm() {
  const values = form.values();
  const issue = problem(values);
  if (issue) {
    setState({ message: issue });
    return { code: 'INVALID', message: issue };
  }
  const changes = Object.fromEntries(FIELDS.filter((f) => values[f] !== shown[f]).map((f) => [f, values[f]]));
  setState({ saving: true, message: 'Saving…' });
  try {
    const result = Object.keys(changes).length ? await api.updateFields(changes) : { code: 'OK', profile: await api.getProfile() };
    if (result.code !== 'OK') {
      setState({ message: `Could not save (${result.code})` });
      return result;
    }
    // Show the saved profile, except in fields the customer has edited again while the save was running.
    for (const f of FIELDS) {
      if (form.input(f).value.trim() === values[f]) form.input(f).value = result.profile[f];
      shown[f] = result.profile[f];
    }
    setState({ profile: result.profile, message: 'Saved' });
    return result;
  } finally {
    setState({ saving: false });
  }
}

// Changes one field. Used by the assistant's update_profile tool.
export async function updateField(field, value) {
  if (!FIELDS.includes(field)) throw new Error(`field must be one of ${FIELDS.join(', ')}`);
  const clean = typeof value === 'string' ? value.trim() : '';
  const issue = problem({ [field]: clean });
  if (issue) return { code: 'INVALID', message: issue };
  const result = await api.updateFields({ [field]: clean });
  if (result.code !== 'OK') return result;
  // Show the change in the form too, unless the customer has typed their own value there.
  if (form.input(field).value.trim() === shown[field]) form.input(field).value = clean;
  shown[field] = clean;
  setState({ profile: result.profile, message: `Your ${field} was updated by the assistant` });
  return { code: 'OK', profile: result.profile };
}

export const currentProfile = () => ({ ...state.profile });
