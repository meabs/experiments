import { update } from './state.js';
import { createScope, isCancelled } from './scope.js';
import { mountEditor } from './editor.js';
import { mountPreview } from './preview.js';

const mounts = { editor: mountEditor, preview: mountPreview };
let scope = null;

// Switches tab: closes the old tab's scope (its tools and requests) and opens the new one.
export async function go(tab) {
  scope?.dispose();
  scope = createScope(tab);
  update({ tab });
  try {
    await mounts[tab](scope);
  } catch (e) {
    if (!isCancelled(e)) update({ message: e.message });
  }
}
