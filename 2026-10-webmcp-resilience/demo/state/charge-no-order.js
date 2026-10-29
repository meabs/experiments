(() => { const s = window.__backend.snapshot(); return { pay: { charges: s.charges, orders: s.orders } }; })()
