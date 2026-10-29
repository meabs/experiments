import * as api from '../api.js';
import { state, setState } from './state.js';
import { FIELDS, problem } from './validate.js';

let form = null;

export function useForm(f) {
  form = f;
}

export async function loadProfile() {
  const profile = await api.getProfile();
  setState({ profile });
  form.fill(profile);
}

// Saves the form. Used by the Save button.
export async function saveForm() {
  const values = form.values();
  const issue = problem(values);
  if (issue) {
    setState({ message: issue });
    return { code: 'INVALID', message: issue };
  }
  setState({ saving: true, message: 'Saving…' });
  try {
    const changes = Object.fromEntries([...form.dirty].map((f) => [f, values[f]]));
    const result = await api.updateFields(changes);
    setState({ profile: result.profile, message: 'Saved' });
    form.fill(result.profile);
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
  setState({ profile: result.profile, message: `Your ${field} was updated by the assistant` });
  return { code: 'OK', profile: result.profile };
}

export const currentProfile = () => ({ ...state.profile });
