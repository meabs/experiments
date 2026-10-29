// Debug log for support: keeps the last 200 events in memory (window.__app.log()).
const events = [];

export function log(event, detail = {}) {
  events.push({ at: new Date().toISOString(), event, ...detail });
  if (events.length > 200) events.shift();
}

export const recent = () => events.slice();
