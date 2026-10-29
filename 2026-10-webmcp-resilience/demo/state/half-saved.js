(() => { const s = window.__backend.snapshot(); return { listing: { title: s.listing.title, description: s.listing.description } }; })()
