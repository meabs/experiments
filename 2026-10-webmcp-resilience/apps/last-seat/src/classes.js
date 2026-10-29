import * as api from '../api.js';
import { state } from './state.js';
import { log } from './log.js';

// Loads the timetable. Called on start, after each booking or cancellation, and every 15 s so seat counts stay fresh.
export async function refreshClasses() {
  const classes = await api.listClasses();
  state.set({ classes });
  return classes;
}

let timer = null;

export function startPolling(everyMs = 15000) {
  stopPolling();
  timer = setInterval(() => {
    refreshClasses().catch((e) => log('poll-failed', { error: String(e) }));
  }, everyMs);
}

export function stopPolling() {
  if (timer) clearInterval(timer);
  timer = null;
}

export const classById = (classId) => state.get().classes.find((c) => c.id === classId);
