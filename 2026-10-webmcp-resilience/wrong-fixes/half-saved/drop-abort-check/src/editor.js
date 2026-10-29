import * as api from '../api.js';
import { update } from './state.js';
import { isCancelled } from './scope.js';
import { keepDraft, clearDraft } from './draft.js';

const $ = (id) => document.getElementById(id);
const fields = () => ({ title: $('title').value, description: $('description').value });

let current = null; // the editor tab's scope while it is open

// Saves the listing. Used by the Save button and by the assistant's save_listing tool.
async function save({ title, description }, scope) {
  if (typeof title !== 'string' || !title.trim()) throw new Error('title must not be empty');
  if (typeof description !== 'string' || !description.trim()) throw new Error('description must not be empty');
  update({ message: 'Saving…' });
  try {
    await api.updateTitle(title.trim(), { signal: scope.signal });
    await api.updateDescription(description.trim(), { signal: scope.signal });
    const listing = await api.getListing({ signal: scope.signal });
    clearDraft();
    update({ listing, message: 'Saved' });
    return { code: 'OK', listing: { title: listing.title, description: listing.description } };
  } catch (e) {
    if (isCancelled(e)) return { code: 'CANCELLED' };
    throw e;
  }
}

async function savePrice(price, scope) {
  const r = await api.updatePrice(Number(price), { signal: scope.signal });
  update({ message: r.code === 'OK' ? 'Price updated' : 'Please enter a price above £0' });
  return r;
}

// Opens the editor tab: fills the form from the server and registers the editor's tools.
export async function mountEditor(scope) {
  current = scope;
  const listing = await api.getListing({ signal: scope.signal });
  $('title').value = listing.title;
  $('description').value = listing.description;
  $('price').value = String(listing.price);
  update({ listing });
  await scope.tools([{
    name: 'save_listing',
    description: 'Save a new title and description for the listing.',
    inputSchema: {
      type: 'object',
      properties: { title: { type: 'string', minLength: 1 }, description: { type: 'string', minLength: 1 } },
      required: ['title', 'description'],
    },
    execute: (input) => save(input, scope),
  }, {
    name: 'set_price',
    description: 'Change the listing price, in pounds.',
    inputSchema: { type: 'object', properties: { price: { type: 'number', exclusiveMinimum: 0 } }, required: ['price'] },
    execute: ({ price }) => savePrice(price, scope),
  }]);
}

export function bindEditor() {
  for (const id of ['title', 'description']) $(id).addEventListener('input', () => keepDraft(fields));
  $('save').addEventListener('click', () => {
    save(fields(), current).catch((e) => update({ message: e.message }));
  });
  $('save-price').addEventListener('click', () => {
    savePrice($('price').value, current).catch((e) => update({ message: e.message }));
  });
}
