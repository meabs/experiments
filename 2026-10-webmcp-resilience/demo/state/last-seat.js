(() => { const s = window.__backend.snapshot()['spin-sat']; return { spin: { booked: s.booked, capacity: s.capacity, over: s.booked - s.capacity } }; })()
