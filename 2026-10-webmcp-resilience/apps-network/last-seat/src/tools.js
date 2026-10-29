import { registerTools } from '../webmcp-host.js';
import * as api from '../api.js';
import { state } from './state.js';
import { bookSeat, cancelSeat, joinWaitlist } from './bookings.js';

const classId = { type: 'string', description: 'Class id from list_classes. Default: spin-sat.' };

// The assistant's WebMCP tools.
export function registerAssistantTools() {
  return registerTools([
    {
      name: 'list_classes',
      description: 'List the classes on the timetable, with capacity and seats booked.',
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => api.listClasses(),
    },
    {
      name: 'get_class',
      description: 'Read one class: name, capacity and seats booked.',
      inputSchema: { type: 'object', properties: { classId } },
      annotations: { readOnlyHint: true },
      execute: ({ classId: id = 'spin-sat' } = {}) => api.getClass(id),
    },
    {
      name: 'book_seat',
      description: 'Book a seat in a class for the named person. Returns code OK with a bookingId, or FULL.',
      inputSchema: {
        type: 'object',
        properties: { name: { type: 'string', minLength: 1 }, classId },
        required: ['name'],
      },
      execute: async ({ name, classId: id = 'spin-sat' }) => {
        const r = await bookSeat(id, name);
        if (r.code === 'OK') state.set({ message: `The assistant booked a seat for ${name.trim()}.` });
        return r;
      },
    },
    {
      name: 'cancel_booking',
      description: 'Cancel a booking made on this page, by bookingId.',
      inputSchema: { type: 'object', properties: { bookingId: { type: 'string' } }, required: ['bookingId'] },
      execute: ({ bookingId }) => cancelSeat(bookingId),
    },
    {
      name: 'join_waitlist',
      description: 'Put the named person on the waiting list for a full class.',
      inputSchema: { type: 'object', properties: { name: { type: 'string', minLength: 1 }, classId }, required: ['name'] },
      execute: ({ name, classId: id = 'spin-sat' }) => joinWaitlist(id, name),
    },
  ]);
}
