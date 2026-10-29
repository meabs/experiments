// WebMCP host. Uses the browser's native document.modelContext when it exists; otherwise installs a small stand-in with
// the same calls (registerTool with an AbortSignal, getTools, executeTool with an AbortSignal), so the page works in any
// Chromium. Do not change this file: it stands in for the browser.
function fallbackModelContext() {
  const tools = [];
  return {
    async registerTool(tool, { signal } = {}) {
      if (tools.some((t) => t.name === tool.name)) throw new Error(`tool ${tool.name} is already registered`);
      tools.push(tool);
      signal?.addEventListener('abort', () => {
        const i = tools.indexOf(tool);
        if (i >= 0) tools.splice(i, 1);
      }, { once: true });
    },
    async getTools() { return [...tools].sort((a, b) => a.name.localeCompare(b.name)); },
    async executeTool(tool, args, { signal } = {}) {
      if (signal?.aborted) throw new DOMException('Tool invocation aborted', 'AbortError');
      const input = typeof args === 'string' ? JSON.parse(args) : (args ?? {});
      return tool.execute(input, { signal });
    },
  };
}

export const nativeWebMCP = Boolean(document.modelContext);
export const host = document.modelContext ?? fallbackModelContext();
if (!nativeWebMCP) {
  Object.defineProperty(host, '__webmcpResilienceCompatibilityHost', { value: true });
  document.modelContext = host;
}

const controllers = new Map();

// Registers tools; returns an AbortController whose abort() unregisters them.
export async function registerTools(tools) {
  const controller = new AbortController();
  await Promise.all(tools.map((tool) => {
    controllers.set(tool.name, controller);
    return host.registerTool(tool, { signal: controller.signal });
  }));
  return controller;
}

// Testing hook used by WebMCP test tools to unregister a tool while a call is running.
host.__webmcpResilienceUnregisterTool = (name) => {
  const c = controllers.get(name);
  if (!c) throw new Error(`tool ${name} has no registration controller`);
  c.abort();
};
