import assert from "node:assert/strict";
import { pathToFileURL, fileURLToPath } from "node:url";
const { load } = await import(pathToFileURL(fileURLToPath(new URL("./_prelude.mjs", import.meta.url))));
const { getDiscountPrice } = await load("src/helpers/product.js");
assert.equal(getDiscountPrice(14, 25), 10.5, "US$14.00 at 25% off is US$10.50");
assert.equal(getDiscountPrice(200, 10), 180);
assert.equal(getDiscountPrice(14, 0), null, "no discount: no sale price");
console.log("ok");
