// Entry point: loads the basket and addresses, draws the page and registers the assistant's tools.
import { get } from './src/state.js';
import { bindControls } from './src/ui.js';
import { refreshQuote, loadAddresses } from './src/quote.js';
import { registerAssistantTools } from './src/tools.js';

bindControls();
window.__app = { getState: () => ({ backend: window.__backend.snapshot(), page: { ...get() } }) };
await Promise.all([refreshQuote(), loadAddresses()]);
await registerAssistantTools();
