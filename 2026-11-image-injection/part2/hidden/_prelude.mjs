// Shared set-up for the hidden tests: okf-local's harness runs the storefront's own modules in plain Node with the
// network (axios), cookies and browser globals stubbed. Run from the workspace root.
import { pathToFileURL, fileURLToPath } from "node:url";
import path from "node:path";
export const H = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../2026-10-okf-local/harness");
await import(pathToFileURL(H + "/env.mjs"));
export const ax = await import(pathToFileURL(H + "/stubs/axios.mjs"));
export const actions = [];
export const dispatch = (a) => (typeof a === "function" ? a(dispatch) : (actions.push(a), a));
export const load = (rel) => import(pathToFileURL(process.cwd() + "/" + rel));
export const cart = () => ({
  cartItems: { code: "C1", quantity: 4, products: [
    { id: 1, sku: "VC-001", quantity: 2, description: { name: "Ceramic Coffee Mug" } },
    { id: 3, sku: "VC-003", quantity: 1, description: { name: "Desk Lamp" } },
    { id: 5, sku: "VC-005", quantity: 1, description: { name: "Wireless Headphones" } }] },
  cartID: "C1", cartCount: 4, orderID: "" });
