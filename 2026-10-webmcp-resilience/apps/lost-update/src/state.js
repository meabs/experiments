// The page's state: the profile as last read from or saved to the server, preferences, and the status message.
const listeners = new Set();
export const state = { profile: {}, preferences: {}, message: '', saving: false };

export function setState(patch) {
  Object.assign(state, patch);
  listeners.forEach((fn) => fn(state));
}

export const watch = (fn) => listeners.add(fn);
