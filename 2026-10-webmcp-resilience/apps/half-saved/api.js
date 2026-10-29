// Simulated backend for the listing editor. It stands in for the marketplace's listing server, which this team does
// not own: do not change this file. Every call takes time (see latency.js). Like fetch, a call can be cancelled with
// options.signal while it is on its way: if the signal aborts before the server has handled the call, the call rejects
// with an AbortError and the server does nothing.
import { wait, seed } from './latency.js';

const db = seed({
  listing: { title: 'Oak bookshelf', description: 'Solid oak, 180 cm tall, five shelves.', price: 120 },
  views: 37,
});

function request(name, { signal } = {}, apply) {
  return new Promise((resolve, reject) => {
    const aborted = () => new DOMException('The request was cancelled', 'AbortError');
    if (signal?.aborted) return reject(aborted());
    let cancelled = false;
    const onAbort = () => { cancelled = true; reject(aborted()); };
    signal?.addEventListener('abort', onAbort, { once: true });
    wait(name).then(() => {
      signal?.removeEventListener('abort', onAbort);
      if (!cancelled) resolve(apply());
    });
  });
}

export const getListing = (options) => request('getListing', options, () => ({ ...db.listing }));

export const getStats = (options) => request('getStats', options, () => ({ views: db.views }));

export const updateTitle = (title, options) => request('updateTitle', options, () => {
  db.listing.title = title;
  return { code: 'OK' };
});

export const updateDescription = (description, options) => request('updateDescription', options, () => {
  db.listing.description = description;
  return { code: 'OK' };
});

export const updatePrice = (price, options) => request('updatePrice', options, () => {
  if (!(price > 0)) return { code: 'BAD_PRICE' };
  db.listing.price = price;
  return { code: 'OK' };
});

// Saves title and description together, in one step on the server.
export const saveListing = ({ title, description }, options) => request('saveListing', options, () => {
  db.listing = { ...db.listing, title, description };
  return { code: 'OK' };
});

// Server-side view, for tests and support staff.
window.__backend = {
  snapshot: () => ({ listing: { title: db.listing.title, description: db.listing.description }, price: db.listing.price }),
};
