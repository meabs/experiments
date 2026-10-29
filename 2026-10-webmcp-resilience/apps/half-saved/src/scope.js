import { registerTools } from '../webmcp-host.js';

// A tab's lifetime. Everything a tab starts (its WebMCP tools, its requests) is tied to its scope's signal, so leaving
// the tab cleans all of it up at once: tools are unregistered and requests still on their way are cancelled.
export function createScope(name) {
  const controller = new AbortController();
  return {
    name,
    signal: controller.signal,
    // Registers tools for as long as the scope lives.
    async tools(list) {
      const registration = await registerTools(list);
      if (controller.signal.aborted) registration.abort();
      else controller.signal.addEventListener('abort', () => registration.abort(), { once: true });
    },
    dispose: () => controller.abort(),
  };
}

export const isCancelled = (e) => e?.name === 'AbortError';
