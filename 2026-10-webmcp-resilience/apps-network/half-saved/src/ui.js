import { onUpdate } from './state.js';
import { go } from './router.js';
import { bindEditor } from './editor.js';

const $ = (id) => document.getElementById(id);

function render(s) {
  $('tab-editor').setAttribute('aria-selected', String(s.tab === 'editor'));
  $('tab-preview').setAttribute('aria-selected', String(s.tab === 'preview'));
  $('editor').hidden = s.tab !== 'editor';
  $('preview').hidden = s.tab !== 'preview';
  $('preview-title').textContent = s.listing.title ?? '';
  $('preview-description').textContent = s.listing.description ?? '';
  $('preview-price').textContent = s.listing.price ? `£${s.listing.price}` : '';
  $('preview-stats').textContent = s.views == null ? '' : `${s.views} people have looked at this listing.`;
  $('message').textContent = s.message;
}

export function bindControls() {
  onUpdate(render);
  bindEditor();
  $('tab-editor').addEventListener('click', () => { void go('editor'); });
  $('tab-preview').addEventListener('click', () => { void go('preview'); });
}
