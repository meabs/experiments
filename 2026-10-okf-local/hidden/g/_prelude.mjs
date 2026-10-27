import { pathToFileURL } from "node:url";
export const H = process.env.OKF_EXP + "/harness";
await import(pathToFileURL(H + "/env.mjs"));
export const ax = await import(pathToFileURL(H + "/stubs/axios.mjs"));
export const dispatch = (a) => (typeof a === "function" ? a(dispatch) : a);
export const noToast = () => {};
export const load = (rel) => import(pathToFileURL(process.cwd() + "/" + rel));
