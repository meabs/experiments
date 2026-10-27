// ESM resolve hook: lets plain Node import the storefront's CRA-style modules (extensionless relative imports) and stubs its npm dependencies.
import { pathToFileURL, fileURLToPath } from "node:url";
import { existsSync, statSync } from "node:fs";
import path from "node:path";
const STUBS = { axios: "axios.mjs", "universal-cookie": "cookie.mjs" };
export async function resolve(specifier, context, next) {
  if (STUBS[specifier]) return { url: pathToFileURL(path.join(path.dirname(fileURLToPath(import.meta.url)), "stubs", STUBS[specifier])).href, shortCircuit: true };
  if ((specifier.startsWith("./") || specifier.startsWith("../")) && context.parentURL) {
    const base = path.resolve(path.dirname(fileURLToPath(context.parentURL)), specifier);
    for (const cand of [base, base + ".js", base + ".mjs", path.join(base, "index.js")]) {
      if (existsSync(cand) && statSync(cand).isFile()) return { url: pathToFileURL(cand).href, shortCircuit: true };
    }
  }
  return next(specifier, context);
}
