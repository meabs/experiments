import { registerTools } from '../webmcp-host.js';
import { FIELDS } from './validate.js';
import { updateField, currentProfile } from './profile.js';
import { setPreference } from './preferences.js';

// The assistant's WebMCP tools.
export function registerAssistantTools() {
  return registerTools([
    {
      name: 'get_profile',
      description: "Read the customer's profile.",
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => currentProfile(),
    },
    {
      name: 'update_profile',
      description: "Change one field of the customer's profile: name, email or phone.",
      inputSchema: {
        type: 'object',
        properties: { field: { type: 'string', enum: FIELDS }, value: { type: 'string', minLength: 1 } },
        required: ['field', 'value'],
      },
      execute: ({ field, value }) => updateField(field, value),
    },
    {
      name: 'set_preference',
      description: 'Turn the newsletter or text-message order updates on or off.',
      inputSchema: {
        type: 'object',
        properties: { key: { type: 'string', enum: ['newsletter', 'sms'] }, value: { type: 'boolean' } },
        required: ['key', 'value'],
      },
      execute: ({ key, value }) => setPreference(key, value),
    },
  ]);
}
