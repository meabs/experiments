// Records every request the storefront code makes and answers from a scripted queue.
export const calls = [];
export const replies = [];
const answer = (method) => async (url, data) => { calls.push({ method, url, data }); const r = replies.shift() ?? {}; return { data: r }; };
const axios = { get: answer("GET"), post: answer("POST"), put: answer("PUT"), delete: answer("DELETE"), patch: answer("PATCH"),
  defaults: {}, interceptors: { request: { use() {} }, response: { use() {} } } };
export default axios;
