// Light checks before anything is sent; the server has its own.
export const FIELDS = ['name', 'email', 'phone'];

const rules = {
  name: (v) => v.length >= 2 || 'Please enter your name',
  email: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Please enter a valid email address',
  phone: (v) => /^[0-9 +()-]{7,}$/.test(v) || 'Please enter a valid phone number',
};

// Returns the first problem with the values given, or null.
export function problem(values) {
  for (const [field, value] of Object.entries(values)) {
    const verdict = rules[field]?.(String(value ?? '').trim());
    if (verdict !== true && verdict !== undefined) return verdict;
  }
  return null;
}
