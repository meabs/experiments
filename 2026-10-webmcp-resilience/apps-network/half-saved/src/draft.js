// Keeps an unsaved draft of the editor in localStorage, so a seller who closes the tab by mistake gets it back.
const KEY = 'listing-draft';

let timer = null;

export function keepDraft(read) {
  clearTimeout(timer);
  timer = setTimeout(() => {
    try { localStorage.setItem(KEY, JSON.stringify({ ...read(), at: Date.now() })); } catch { /* storage full or blocked */ }
  }, 500);
}

export function takeDraft() {
  try {
    const d = JSON.parse(localStorage.getItem(KEY) ?? 'null');
    return d && Date.now() - d.at < 24 * 3600 * 1000 ? d : null;
  } catch {
    return null;
  }
}

export function clearDraft() {
  clearTimeout(timer);
  try { localStorage.removeItem(KEY); } catch { /* ignore */ }
}
