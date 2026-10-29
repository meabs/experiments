// Simulated backend for the account page. It stands in for the shop's customer server, which this team does not own:
// do not change this file. Every call takes time (see latency.js).
import { wait, seed } from './latency.js';

const db = seed({
  profile: { name: 'Sam Jones', email: 'sam@example.com', phone: '01632 960001' },
  preferences: { newsletter: true, sms: false },
});
const FIELDS = ['name', 'email', 'phone'];

export async function getProfile() {
  await wait('getProfile');
  return { ...db.profile };
}

// Replaces the whole profile with the values given.
export async function saveProfile(profile) {
  await wait('saveProfile');
  db.profile = { name: profile.name, email: profile.email, phone: profile.phone };
  return { code: 'OK', profile: { ...db.profile } };
}

// Changes only the fields given, e.g. { phone: '...' }.
export async function updateFields(fields) {
  await wait('updateFields');
  for (const k of Object.keys(fields)) {
    if (!FIELDS.includes(k)) return { code: 'UNKNOWN_FIELD', field: k };
  }
  Object.assign(db.profile, fields);
  return { code: 'OK', profile: { ...db.profile } };
}

export async function getPreferences() {
  await wait('getPreferences');
  return { ...db.preferences };
}

export async function setPreference(key, value) {
  await wait('setPreference');
  if (!(key in db.preferences)) return { code: 'UNKNOWN_PREFERENCE' };
  db.preferences[key] = Boolean(value);
  return { code: 'OK', preferences: { ...db.preferences } };
}

// Server-side view, for tests and support staff.
window.__backend = { snapshot: () => ({ profile: { ...db.profile }, preferences: { ...db.preferences } }) };
