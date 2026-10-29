// Product analytics: events are batched and sent every few seconds (here, kept in memory for window.__app.events()).
const queue = [];
const sent = [];
let timer = null;

export function track(event, props = {}) {
  queue.push({ event, ...props, at: Date.now() });
  timer ??= setTimeout(flush, 3000);
}

function flush() {
  sent.push(...queue.splice(0));
  timer = null;
}

export const events = () => [...sent, ...queue];
