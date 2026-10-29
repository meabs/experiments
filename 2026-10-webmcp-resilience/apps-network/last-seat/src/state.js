// The page's state, in one small observable store. Modules read it with state.get() and change it with state.set();
// the view re-renders on every change.
function createStore(initial) {
  let current = initial;
  const listeners = new Set();
  return {
    get: () => current,
    set(patch) {
      current = { ...current, ...patch };
      for (const fn of listeners) fn(current);
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
  };
}

export const state = createStore({
  classes: [], // from the server: { id, name, capacity, booked, version }
  selected: 'spin-sat',
  mine: [], // bookings made on this page: { id, classId, name }
  busy: false, // the Book button is working
  message: '',
  offerWaitlist: false,
});
