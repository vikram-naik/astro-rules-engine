// ------------------------------------------------------------
// i18n loader  (can be moved to a separate i18n.js)
// ------------------------------------------------------------
(async function i18nInit() {
  const defaultLocale  = "gu";
  const fallbackLocale = "en";

  async function fetchLocale(locale) {
    try {
      const res = await fetch(`/static/i18n/${locale}.json`);
      if (!res.ok) throw new Error("no locale");
      return await res.json();
    } catch {
      return null;
    }
  }

  async function applyLocale(locale) {
    const dict = (await fetchLocale(locale)) || {};
    const fb   = (await fetchLocale(fallbackLocale)) || {};
    const merged = Object.assign({}, fb, dict);

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.dataset.i18n;
      const txt = key.split(".").reduce((o, k) => (o && o[k]) ? o[k] : null, merged);
      if (txt != null) {
        if (el.dataset.i18nHtml !== undefined) el.innerHTML = txt;
        else el.textContent = txt;
      }
    });
    if (merged._meta?.dir) document.documentElement.dir = merged._meta.dir;
    localStorage.setItem("wb:locale", locale);
  }

  let locale = localStorage.getItem("wb:locale") || defaultLocale;
  const ok = await fetchLocale(locale);
  await applyLocale(ok ? locale : fallbackLocale);

  const langSel = document.getElementById("langSelect");
  if (langSel)
    langSel.addEventListener("change", async () => await applyLocale(langSel.value));
})();