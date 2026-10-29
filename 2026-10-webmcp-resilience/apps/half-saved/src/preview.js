import * as api from '../api.js';
import { update } from './state.js';

// Opens the preview tab: shows the listing as buyers see it, and registers the preview's tools.
export async function mountPreview(scope) {
  const [listing, stats] = await Promise.all([api.getListing({ signal: scope.signal }), api.getStats({ signal: scope.signal })]);
  update({ listing, views: stats.views });
  await scope.tools([{
    name: 'get_listing',
    description: 'Read the listing as buyers see it.',
    inputSchema: { type: 'object', properties: {} },
    annotations: { readOnlyHint: true },
    execute: () => api.getListing({ signal: scope.signal }),
  }]);
}
