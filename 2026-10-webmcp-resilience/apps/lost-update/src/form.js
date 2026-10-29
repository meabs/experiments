import { FIELDS } from './validate.js';

// The details form. Knows which fields the customer has touched since it was last filled, to show the "unsaved changes"
// note and to warn before leaving the page.
export class DetailsForm {
  constructor(root) {
    this.root = root;
    this.dirty = new Set();
    this.onDirtyChange = () => {};
    for (const f of FIELDS) {
      this.input(f).addEventListener('input', () => {
        this.dirty.add(f);
        this.onDirtyChange(this.dirty.size > 0);
      });
    }
    window.addEventListener('beforeunload', (e) => {
      if (this.dirty.size) e.preventDefault();
    });
  }

  input(field) {
    return this.root.querySelector(`[name="${field}"]`);
  }

  // Puts a profile into the form and forgets what was touched.
  fill(profile) {
    for (const f of FIELDS) this.input(f).value = profile[f] ?? '';
    this.dirty.clear();
    this.onDirtyChange(false);
  }

  values() {
    return Object.fromEntries(FIELDS.map((f) => [f, this.input(f).value.trim()]));
  }
}
