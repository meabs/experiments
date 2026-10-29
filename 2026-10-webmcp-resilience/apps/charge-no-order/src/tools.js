import { registerTools } from '../webmcp-host.js';
import * as api from '../api.js';
import { placeOrder } from './checkout.js';
import { chooseDelivery } from './quote.js';

// The assistant's WebMCP tools.
export function registerAssistantTools() {
  return registerTools([
    {
      name: 'get_total',
      description: 'Read the basket lines, delivery address and total.',
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => api.getQuote(),
    },
    {
      name: 'set_delivery_address',
      description: 'Choose where the order is delivered: home or work.',
      inputSchema: { type: 'object', properties: { addressId: { type: 'string', enum: ['home', 'work'] } }, required: ['addressId'] },
      execute: ({ addressId }) => chooseDelivery(addressId),
    },
    {
      name: 'place_order',
      description: 'Place the order for the current basket and pay with the saved card. Returns code OK with an orderId, ' +
        'or CANCELLED if the call was cancelled.',
      inputSchema: { type: 'object', properties: {} },
      annotations: { consequentialHint: true },
      execute: (_input, { signal } = {}) => placeOrder({ signal }),
    },
    {
      name: 'get_order_status',
      description: 'Read the status of an order.',
      inputSchema: { type: 'object', properties: { orderId: { type: 'string' } }, required: ['orderId'] },
      annotations: { readOnlyHint: true },
      execute: ({ orderId }) => api.getOrder(orderId),
    },
  ]);
}
