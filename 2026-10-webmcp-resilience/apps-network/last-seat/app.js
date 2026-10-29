// Entry point: wires the store, the view, the controls and the assistant's tools together.
import { state } from './src/state.js';
import { render, bindControls } from './src/ui.js';
import { refreshClasses, startPolling } from './src/classes.js';
import { registerAssistantTools } from './src/tools.js';
import { recent } from './src/log.js';

state.subscribe(render);
bindControls();
window.__app = { getState: () => ({ backend: window.__backend.snapshot(), page: { ...state.get() } }), log: recent };
await refreshClasses();
await registerAssistantTools();
startPolling();
