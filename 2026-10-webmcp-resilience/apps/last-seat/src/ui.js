import { state } from './state.js';
import { bookSeat, cancelSeat, joinWaitlist } from './bookings.js';
import { classById } from './classes.js';

const $ = (id) => document.getElementById(id);

function li(text, button) {
  const item = document.createElement('li');
  item.textContent = text;
  if (button) item.append(' ', button);
  return item;
}

export function render(s) {
  $('classes').replaceChildren(...s.classes.map((c) => li(`${c.name}: ${c.booked} of ${c.capacity} seats booked`)));
  const select = $('class');
  if (select.options.length !== s.classes.length) {
    select.replaceChildren(...s.classes.map((c) => new Option(c.name, c.id)));
  }
  select.value = s.selected;
  $('mine').replaceChildren(...s.mine.map((b) => {
    const cancel = document.createElement('button');
    cancel.textContent = 'Cancel';
    cancel.addEventListener('click', () => { void cancelSeat(b.id); });
    return li(`${classById(b.classId)?.name ?? b.classId} for ${b.name}`, cancel);
  }));
  $('book').disabled = s.busy;
  $('waitlist').hidden = !s.offerWaitlist;
  $('message').textContent = s.message;
}

export function bindControls() {
  $('class').addEventListener('change', (e) => state.set({ selected: e.target.value, offerWaitlist: false, message: '' }));

  $('book').addEventListener('click', async () => {
    if (state.get().busy) return; // ignore double clicks while a booking is going through
    const { selected } = state.get();
    state.set({ busy: true, message: 'Booking…', offerWaitlist: false });
    try {
      const r = await bookSeat(selected, $('person').value);
      if (r.code === 'OK') state.set({ message: 'Booked. See you there!' });
      else if (r.code === 'FULL') state.set({ message: `Sorry, ${classById(selected)?.name} is full.`, offerWaitlist: true });
      else state.set({ message: `Could not book (${r.code}).` });
    } catch (e) {
      state.set({ message: e.message });
    } finally {
      state.set({ busy: false });
    }
  });

  $('waitlist').addEventListener('click', async () => {
    const r = await joinWaitlist(state.get().selected, $('person').value);
    state.set({ message: r.code === 'OK' ? `You are number ${r.position} on the waiting list.` : r.code, offerWaitlist: false });
  });
}
