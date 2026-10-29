// Entry point: loads the catalogue and basket, draws the page and registers the assistant's tools.
import * as api from './api.js';
import { state, update } from './src/state.js';
import { renderProducts, bindControls } from './src/ui.js';
import { refreshBasket } from './src/basket.js';
import { registerAssistantTools } from './src/tools.js';
import { events } from './src/analytics.js';

bindControls();
window.__app = { getState: () => ({ basket: window.__backend.snapshot().lines, page: { message: state.message } }), events };
update({ products: await api.getProducts() });
renderProducts();
await refreshBasket();
await registerAssistantTools();
