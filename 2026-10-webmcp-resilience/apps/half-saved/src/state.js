// The page's state. update() merges a change and re-renders.
const listeners = [];
export const state = { tab: 'editor', listing: {}, views: null, message: '' };

export function update(change) {
  Object.assign(state, change);
  listeners.forEach((fn) => fn(state));
}

export const onUpdate = (fn) => listeners.push(fn);
