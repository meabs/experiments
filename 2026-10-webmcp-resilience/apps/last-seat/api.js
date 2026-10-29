// Simulated backend for the class-booking page. It stands in for the gym's booking server, which this team does not
// own: do not change this file. Every call takes time (see latency.js). Other customers book through the same server
// from the gym's app and the front desk at any time, not only through this page.
import { wait, seed } from './latency.js';

const db = seed({
  classes: [
    { id: 'spin-sat', name: 'Saturday spin class', capacity: 1 },
    { id: 'yoga-sun', name: 'Sunday yoga', capacity: 12 },
    { id: 'hiit-mon', name: 'Monday HIIT', capacity: 8 },
  ],
  bookings: [], // { id, classId, name }
  waitlist: [], // { classId, name }
});
const version = Object.fromEntries(db.classes.map((c) => [c.id, 1]));
let nextId = 1;

const find = (classId) => db.classes.find((c) => c.id === classId);
const bookedIn = (classId) => db.bookings.filter((b) => b.classId === classId).length;
const info = (c) => ({ id: c.id, name: c.name, capacity: c.capacity, booked: bookedIn(c.id), version: version[c.id] });

function add(classId, name) {
  const booking = { id: `b${nextId++}`, classId, name };
  db.bookings.push(booking);
  version[classId]++;
  return booking;
}

// Every class, with capacity and seats booked.
export async function listClasses() {
  await wait('listClasses');
  return db.classes.map(info);
}

// One class: capacity, seats booked, and its version, a number that changes whenever a booking in the class is made or
// cancelled.
export async function getClass(classId) {
  await wait('getClass');
  const c = find(classId);
  return c ? info(c) : { code: 'UNKNOWN_CLASS' };
}

// Adds a booking. The server does not check capacity. With options.ifVersion (a version from getClass), the booking is
// made only if the class is still at that version; otherwise nothing is booked and the answer is
// { code: 'CONFLICT', version: <current version> }.
export async function createBooking(classId, name, options = {}) {
  await wait('createBooking');
  if (!find(classId)) return { code: 'UNKNOWN_CLASS' };
  if (options.ifVersion != null && options.ifVersion !== version[classId]) {
    return { code: 'CONFLICT', version: version[classId] };
  }
  return { code: 'OK', ...add(classId, name) };
}

export async function cancelBooking(bookingId) {
  await wait('cancelBooking');
  const i = db.bookings.findIndex((b) => b.id === bookingId);
  if (i < 0) return { code: 'UNKNOWN_BOOKING' };
  const [b] = db.bookings.splice(i, 1);
  version[b.classId]++;
  return { code: 'OK' };
}

export async function joinWaitlist(classId, name) {
  await wait('joinWaitlist');
  if (!find(classId)) return { code: 'UNKNOWN_CLASS' };
  if (!db.waitlist.some((w) => w.classId === classId && w.name === name)) db.waitlist.push({ classId, name });
  return { code: 'OK', position: db.waitlist.filter((w) => w.classId === classId).length };
}

// Server-side view and test hooks, for tests and support staff. otherCustomerBooks(classId, name, inMs): another
// customer books from the gym's app in `inMs` ms (the app books only if a seat is free).
window.__backend = {
  snapshot: () => Object.fromEntries(db.classes.map((c) => [c.id, {
    capacity: c.capacity, booked: bookedIn(c.id), names: db.bookings.filter((b) => b.classId === c.id).map((b) => b.name),
  }])),
  otherCustomerBooks: (classId, name, inMs = 0) => setTimeout(() => {
    const c = find(classId);
    if (c && bookedIn(classId) < c.capacity) add(classId, name);
  }, inMs),
};
