// Entry point: loads the basket line, draws the page and registers the assistant's tools.
import { view } from './src/state.js';
import { bindControls } from './src/ui.js';
import { loadLine } from './src/quantity.js';
import { checkStock } from './src/stock.js';
import { registerAssistantTools } from './src/tools.js';

bindControls();
window.__app = { getState: () => ({ backend: window.__backend.snapshot(), page: { quantity: view.quantity } }) };
await loadLine();
void checkStock();
await registerAssistantTools();
