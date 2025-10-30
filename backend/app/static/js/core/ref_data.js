/* core/ref_data.js
 *
 * Shared loaders for reference & sectors data.
 * Exports:
 *   loadReference() -> ensures window.REF is populated
 *   loadSectors()   -> ensures window.SECTORS is populated
 *
 * Both are idempotent and safe to call from multiple modules.
 */

import { toast, fetchJSON } from "./utils.js";

let __loadingRef = null;
let __loadingSectors = null;

export async function loadReference() {
  // idempotent: return in-flight or already-loaded
  if (window.REF) return window.REF;
  if (__loadingRef) return __loadingRef;

  __loadingRef = (async () => {
    try {
      const data = await fetchJSON("/api/reference/");
      window.REF = data || { planets: [], relations: [], effects: [], signs: [] };
      return window.REF;
    } catch (err) {
      console.error("astro_data: loadReference failed", err);
      toast("Failed to load reference data", "danger");
      window.REF = { planets: [], relations: [], effects: [], signs: [] };
      return window.REF;
    } finally {
      __loadingRef = null;
    }
  })();

  return __loadingRef;
}

export async function loadSectors(force = false) {
  // If not forcing and already loaded, return cached version
  if (!force && window.SECTORS) return window.SECTORS;
  if (!force && __loadingSectors) return __loadingSectors;

  __loadingSectors = (async () => {
    try {
      const data = await fetchJSON("/api/sectors");
      window.SECTORS = Array.isArray(data) ? data : [];
      return window.SECTORS;
    } catch (err) {
      console.error("ref_data: loadSectors failed", err);
      toast("Failed to load sectors", "danger");
      window.SECTORS = [];
      return window.SECTORS;
    } finally {
      __loadingSectors = null;
    }
  })();

  return __loadingSectors;
}

