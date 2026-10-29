import { state, setState, watch } from './state.js';
import { saveForm } from './profile.js';
import { setPreference } from './preferences.js';

const $ = (id) => document.getElementById(id);

function render(s) {
  const p = s.profile;
  $('card').textContent = p.name ? `${p.name} · ${p.email} · ${p.phone}` : '';
  $('save').disabled = s.saving;
  $('newsletter').checked = Boolean(s.preferences.newsletter);
  $('sms').checked = Boolean(s.preferences.sms);
  $('message').textContent = s.message;
}

export function bindControls(form) {
  watch(render);
  form.onDirtyChange = (dirty) => { $('unsaved').hidden = !dirty; };
  $('details').addEventListener('submit', (e) => {
    e.preventDefault();
    saveForm().catch((err) => setState({ message: err.message }));
  });
  for (const key of ['newsletter', 'sms']) {
    $(key).addEventListener('change', (e) => { void setPreference(key, e.target.checked); });
  }
  render(state);
}
