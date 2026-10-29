// Entry point: draws the page and opens the editor tab (each tab registers its own WebMCP tools).
import { state } from './src/state.js';
import { bindControls } from './src/ui.js';
import { go } from './src/router.js';
import { takeDraft } from './src/draft.js';

bindControls();
window.__app = { getState: () => ({ backend: window.__backend.snapshot(), page: { tab: state.tab, message: state.message } }) };
await go('editor');
if (takeDraft()) document.getElementById('draft-note').textContent = 'You have an unsaved draft from earlier.';
