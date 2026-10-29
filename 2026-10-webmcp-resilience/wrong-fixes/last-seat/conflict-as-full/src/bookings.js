import * as api from '../api.js';
import { state } from './state.js';
import { refreshClasses } from './classes.js';
import { log } from './log.js';

function cleanName(name) {
  if (typeof name !== 'string' || !name.trim()) throw new Error('name must be a non-empty string');
  return name.trim().replace(/\s+/g, ' ');
}

// Books a seat in a class for `name`. Used by the Book button and by the assistant's book_seat tool.
// Returns { code: 'OK', bookingId }, { code: 'FULL' } or { code: 'UNKNOWN_CLASS' }.
export async function bookSeat(classId, name) {
  const who = cleanName(name);
  const cls = await api.getClass(classId);
  if (cls.code) return cls;
  if (cls.booked >= cls.capacity) {
    log('full', { classId, who });
    return { code: 'FULL' };
  }
  const booking = await api.createBooking(classId, who, { ifVersion: cls.version });
  if (booking.code === 'CONFLICT') return { code: 'FULL' };
  if (booking.code !== 'OK') return booking;
  log('booked', { classId, who, id: booking.id });
  state.set({ mine: [...state.get().mine, { id: booking.id, classId, name: who }] });
  await refreshClasses();
  return { code: 'OK', bookingId: booking.id };
}

export async function cancelSeat(bookingId) {
  const result = await api.cancelBooking(bookingId);
  if (result.code === 'OK') state.set({ mine: state.get().mine.filter((b) => b.id !== bookingId) });
  await refreshClasses();
  return result;
}

export async function joinWaitlist(classId, name) {
  const who = cleanName(name);
  const result = await api.joinWaitlist(classId, who);
  log('waitlist', { classId, who, ...result });
  return result;
}
