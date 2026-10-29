import { registerTools } from '../webmcp-host.js';
import * as api from '../api.js';
import { view } from './state.js';
import { setQuantity } from './quantity.js';
import { estimate } from './delivery.js';

// The assistant's WebMCP tools.
export function registerAssistantTools() {
  return registerTools([
    {
      name: 'get_basket_line',
      description: 'Read the basket line: product, price and quantity.',
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => api.getLine(view.sku),
    },
    {
      name: 'set_quantity',
      description: 'Set how many of a basket line the customer wants (1 to 99).',
      inputSchema: {
        type: 'object',
        properties: { sku: { type: 'string', enum: [view.sku] }, quantity: { type: 'integer', minimum: 1, maximum: 99 } },
        required: ['sku', 'quantity'],
      },
      execute: ({ quantity }) => setQuantity(quantity, 'assistant'),
    },
    {
      name: 'delivery_estimate',
      description: 'Estimate delivery time, in working days, to a UK postcode.',
      inputSchema: { type: 'object', properties: { postcode: { type: 'string' } }, required: ['postcode'] },
      annotations: { readOnlyHint: true },
      execute: ({ postcode }) => estimate(postcode),
    },
  ]);
}
