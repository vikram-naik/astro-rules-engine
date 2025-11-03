/* core/i18n.js
 *
 * Handles multilingual label translation for the Workbench UI.
 *
 * Exports:
 *   initI18n()        – Initialize and apply saved or default locale
 *   applyLocale(code) – Change language at runtime
 *   t(key) / safeT(key)
 *
 * Automatically updates:
 *   - [data-i18n] text content
 *   - [data-i18n-html] innerHTML
 *   - [data-i18n-title] title attributes
 *   - [data-i18n-placeholder] placeholder attributes
 *   - <option data-i18n> dropdown options
 */

import { toast } from "./utils.js";

const DEFAULT_LOCALE = "gu";
const FALLBACK_LOCALE = "en";
let currentDict = {};
let fallbackDict = {};

/* -------------------------------------------------------------------------- */
/* 🧩 Utilities */
/* -------------------------------------------------------------------------- */

/** Fetch a locale JSON file safely */
async function fetchLocale(locale) {
  try {
    const res = await fetch(`/static/i18n/${locale}.json`, { cache: "no-store" });
    if (!res.ok) throw new Error("missing locale");
    return await res.json();
  } catch {
    console.warn(`⚠️  i18n: could not load locale ${locale}`);
    return null;
  }
}

/** Resolve nested key "a.b.c" → value */
function resolveKey(key, dict) {
  return key.split(".").reduce((o, k) => (o && o[k] ? o[k] : null), dict);
}

/* -------------------------------------------------------------------------- */
/* 🔤 DOM translation functions */
/* -------------------------------------------------------------------------- */

/** Translate all DOM elements marked with i18n attributes */
function translateDom(dict, fb) {
  try {
    // Standard text or innerHTML translations
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.dataset.i18n;
      const txt = resolveKey(key, dict) ?? resolveKey(key, fb) ?? el.textContent;
      if (txt !== null && txt !== undefined) {
        if (el.dataset.i18nHtml !== undefined) el.innerHTML = txt;
        else el.textContent = txt;
      }
    });

    // Title attributes
    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const key = el.dataset.i18nTitle;
      const txt = resolveKey(key, dict) ?? resolveKey(key, fb);
      if (txt) el.title = txt;
    });

    // Placeholder attributes
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.dataset.i18nPlaceholder;
      const txt = resolveKey(key, dict) ?? resolveKey(key, fb);
      if (txt) el.placeholder = txt;
    });

    // Text direction (optional)
    if (dict._meta?.dir) document.documentElement.dir = dict._meta.dir;
  } catch (e) {
    console.warn("i18n translateDom failed:", e);
  }
}

/** Refresh <option data-i18n> elements dynamically when locale changes */
function refreshI18nOptions(dict = currentDict, fb = fallbackDict) {
  try {
    document.querySelectorAll("option[data-i18n]").forEach((opt) => {
      const key = opt.dataset.i18n;
      if (key) {
        const txt = resolveKey(key, dict) ?? resolveKey(key, fb) ?? opt.textContent;
        if (txt) opt.textContent = txt;
      }
    });
  } catch (e) {
    console.warn("i18n refreshI18nOptions failed:", e);
  }
}

/* -------------------------------------------------------------------------- */
/* 🌐 Locale application */
/* -------------------------------------------------------------------------- */

/** Apply and persist a given locale code */
export async function applyLocale(locale) {
  const dict = (await fetchLocale(locale)) || {};
  const fb = fallbackDict || (await fetchLocale(FALLBACK_LOCALE)) || {};
  currentDict = dict;

  // 🔄 Apply all translation layers
  translateDom(dict, fb);
  refreshI18nOptions(dict, fb);

  try {
    localStorage.setItem("wb:locale", locale);
  } catch (_) {}

  const langSel = document.getElementById("langSelect");
  if (langSel && langSel.value !== locale) langSel.value = locale;

  toast(
    dict._meta?.changedMessage ||
      (locale === "gu" ? "ભાષા બદલાઈ" : "Language changed"),
    "info",
    { duration: 1200 }
  );

  // 🔔 Notify registered listeners
  localeChangeListeners.forEach((fn) => {
    try {
      fn(locale);
    } catch (e) {
      console.warn("i18n localeChange handler failed:", e);
    }
  });
}

/* -------------------------------------------------------------------------- */
/* 🔍 Translators for code usage */
/* -------------------------------------------------------------------------- */

/** t(key) - lookup in currentDict then fallbackDict */
export function t(key) {
  if (!key || typeof key !== "string") return null;
  const val = resolveKey(key, currentDict);
  if (val !== null && val !== undefined) return val;
  return resolveKey(key, fallbackDict);
}

/** safeT(key) - returns key itself if translation missing */
export function safeT(key) {
  try {
    const v = t(key);
    return v ?? key;
  } catch {
    return key;
  }
}

/* -------------------------------------------------------------------------- */
/* 🚀 Initialization */
/* -------------------------------------------------------------------------- */

/** Initialize i18n system (on DOM ready) */
export async function initI18n() {
  fallbackDict = (await fetchLocale(FALLBACK_LOCALE)) || {};
  const stored = localStorage.getItem("wb:locale");
  let locale = stored || DEFAULT_LOCALE;

  let dict = await fetchLocale(locale);
  if (!dict) {
    locale = DEFAULT_LOCALE;
    dict = (await fetchLocale(locale)) || fallbackDict;
  }

  currentDict = dict;
  translateDom(dict, fallbackDict);
  refreshI18nOptions(dict, fallbackDict);

  // --- Language selector handling ---
  const langSel = document.getElementById("langSelect");
  if (langSel) {
    langSel.value = locale;
    langSel.addEventListener("change", (e) => applyLocale(e.target.value));
  }

  try {
    localStorage.setItem("wb:locale", locale);
  } catch (_) {}

  console.info(`🌐 i18n initialized: ${locale}`);
}

/* -------------------------------------------------------------------------- */
/* 📣 Locale change listener registry */
/* -------------------------------------------------------------------------- */

const localeChangeListeners = [];

export function onLocaleChange(callback) {
  if (typeof callback === "function") localeChangeListeners.push(callback);
}

/* -------------------------------------------------------------------------- */
/* 🧩 Helper for dynamically added content */
/* -------------------------------------------------------------------------- */

/** Translate newly added DOM fragments */
export function translateNewContent(container = document) {
  try {
    if (!container) container = document;
    translateDom(currentDict, fallbackDict);
    refreshI18nOptions(currentDict, fallbackDict);
  } catch (e) {
    console.warn("i18n translateNewContent failed:", e);
  }
}

/* -------------------------------------------------------------------------- */
/* 🧭 Backward compatibility globals */
/* -------------------------------------------------------------------------- */
if (typeof window !== "undefined") {
  window.initI18n = initI18n;
  window.applyLocale = applyLocale;
}
