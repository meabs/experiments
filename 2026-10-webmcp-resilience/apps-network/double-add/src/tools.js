import { registerTools } from '../webmcp-host.js';
import { state } from './state.js';
import { addToCart, removeFromCart, refreshBasket } from './basket.js';

// The assistant's WebMCP tools.
export function registerAssistantTools() {
  return registerTools([
    {
      name: 'list_products',
      description: 'List the products for sale, with sku, name and price.',
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => state.products,
    },
    {
      name: 'add_to_cart',
      description: 'Add a product to the basket. requestId identifies this request: if a call times out or its result is ' +
        'lost, the assistant calls again with the same requestId, and the product must only be added once.',
      inputSchema: {
        type: 'object',
        properties: {
          sku: { type: 'string' },
          quantity: { type: 'integer', minimum: 1 },
          requestId: { type: 'string', minLength: 1 },
        },
        required: ['sku', 'requestId'],
      },
      execute: (input) => addToCart({ ...input, source: 'assistant' }),
    },
    {
      name: 'remove_from_cart',
      description: 'Remove a product from the basket.',
      inputSchema: { type: 'object', properties: { sku: { type: 'string' } }, required: ['sku'] },
      execute: ({ sku }) => removeFromCart(sku),
    },
    {
      name: 'get_basket',
      description: 'Read the basket lines and totals.',
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => refreshBasket(),
    },
  ]);
}
