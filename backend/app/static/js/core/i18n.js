/* core/i18n.js
 *
 * Handles multilingual label translation for the Workbench UI.
 * 
 * Exports:
 *   initI18n()        – Initialize and apply saved or default locale
 *   applyLocale(code) – Change language at runtime
 *
 * For backward compatibility, both are also assigned to window.*
 */

import { toast } from "./utils.js";

const DEFAULT_LOCALE = "gu";
const FALLBACK_LOCALE = "en";
let currentDict = {};
let fallbackDict = {};

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

/** Apply translations from loaded dictionary */
function translateDom(dict, fb) {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
        const key = el.dataset.i18n;
        const txt =
            resolveKey(key, dict) ?? resolveKey(key, fb) ?? el.textContent;
        if (txt !== null) {
            if (el.dataset.i18nHtml !== undefined) el.innerHTML = txt;
            else el.textContent = txt;
        }
    });
    if (dict._meta?.dir) document.documentElement.dir = dict._meta.dir;
}

/** Apply a given locale code */
export async function applyLocale(locale) {
    const dict = (await fetchLocale(locale)) || {};
    const fb = fallbackDict || (await fetchLocale(FALLBACK_LOCALE)) || {};
    currentDict = dict;
    translateDom(dict, fb);
    try {
        localStorage.setItem("wb:locale", locale);
    } catch (_) { }
    const langSel = document.getElementById("langSelect");
    if (langSel && langSel.value !== locale) langSel.value = locale;
    toast(
        dict._meta?.changedMessage ||
        (locale === "gu" ? "ભાષા બદલી" : "Language changed"),
        "info",
        { duration: 1200 }
    );
}


/**
 * t(key) - lookup in currentDict then fallbackDict, returns null if missing
 * kept minimal so other modules can call t(...) directly if they want.
 */
export function t(key) {
    if (!key || typeof key !== "string") return null;
    const val = resolveKey(key, currentDict);
    if (val !== null && val !== undefined) return val;
    const fb = fallbackDict || {};
    return resolveKey(key, fb);
}

/**
 * Safe translator for external libraries (e.g., AG Grid)
 * Returns key itself if translation missing.
 */
export function safeT(key) {
    try {
        const v = t(key);
        return v ?? key;
    } catch {
        return key;
    }
}


/** Initialize i18n system (on DOM ready) */
export async function initI18n() {
    fallbackDict = (await fetchLocale(FALLBACK_LOCALE)) || {};
    const stored = localStorage.getItem("wb:locale");
    let locale = stored || DEFAULT_LOCALE;

    // Load chosen locale (fallback to DEFAULT if missing)
    let dict = await fetchLocale(locale);
    if (!dict) {
        locale = DEFAULT_LOCALE;
        dict = (await fetchLocale(locale)) || fallbackDict;
    }

    currentDict = dict;
    translateDom(dict, fallbackDict);

    // --- Language selector handling ---
    const langSel = document.getElementById("langSelect");
    if (langSel) {
        // ensure dropdown reflects the active locale right away
        langSel.value = locale;
        langSel.addEventListener("change", (e) => applyLocale(e.target.value));
    }

    try {
        localStorage.setItem("wb:locale", locale);
    } catch (_) { }

    console.info(`🌐 i18n initialized: ${locale}`);
}

/** Notify components (like AG Grid) when locale changes */
const localeChangeListeners = [];

export function onLocaleChange(callback) {
    if (typeof callback === "function") localeChangeListeners.push(callback);
}

/* patch applyLocale to trigger listener callbacks */
const _applyLocale = applyLocale;
applyLocale = async function (locale) {
    await _applyLocale(locale);
    localeChangeListeners.forEach(fn => {
        try { fn(locale); } catch (e) { console.warn("i18n localeChange handler failed:", e); }
    });
};

/* Backward compatibility globals */
if (typeof window !== "undefined") {
    window.initI18n = initI18n;
    window.applyLocale = applyLocale;
}


