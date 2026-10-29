// Entry point: loads the customer's details, draws the page and registers the assistant's tools.
import { state } from './src/state.js';
import { DetailsForm } from './src/form.js';
import { bindControls } from './src/ui.js';
import { useForm, loadProfile } from './src/profile.js';
import { loadPreferences } from './src/preferences.js';
import { registerAssistantTools } from './src/tools.js';

const form = new DetailsForm(document.getElementById('details'));
useForm(form);
bindControls(form);
window.__app = { getState: () => ({ backend: window.__backend.snapshot(), page: { ...state, form: form.values() } }) };
await Promise.all([loadProfile(), loadPreferences()]);
await registerAssistantTools();
