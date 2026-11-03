import assert from "node:assert/strict";
import { pathToFileURL, fileURLToPath } from "node:url";
const { load, ax, dispatch, actions } = await import(pathToFileURL(fileURLToPath(new URL("./_prelude.mjs", import.meta.url))));
const { getCart, GET_CART } = await load("src/redux/actions/cartActions.js");
const reply = { code: "C1", quantity: 4, products: [{ id: 1, quantity: 4 }] };
for (const saved of [null, JSON.stringify({ cartData: { cartID: "C1" } })]) {   // fresh browser: no language chosen yet
  if (saved === null) localStorage.removeItem("redux_localstorage_simple"); else localStorage.setItem("redux_localstorage_simple", saved);
  ax.calls.length = 0; actions.length = 0; ax.replies.push(reply);
  await getCart("C1", null)(dispatch);
  const get = ax.calls.find((c) => c.method === "GET");
  assert.ok(get, "no GET request for the cart was sent");
  assert.equal(get.url, "cart/C1?lang=en", "with no language chosen, the cart is fetched in English");
  assert.ok(actions.some((a) => a.type === GET_CART && a.payload.code === "C1"), "the fetched cart was not stored");
}
localStorage.setItem("redux_localstorage_simple", JSON.stringify({ multilanguage: { currentLanguageCode: "fr" } }));
ax.calls.length = 0; actions.length = 0; ax.replies.push(reply);
await getCart("C1", null)(dispatch);
assert.equal(ax.calls.find((c) => c.method === "GET")?.url, "cart/C1?lang=fr", "a chosen language is still used");
console.log("ok");
