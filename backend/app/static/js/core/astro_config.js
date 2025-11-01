/* core/astro_config.js
 * 
 * Manages Astro configuration (ayanamsa, lon, lat, alt, tz).
 * Now also manages provider, max_workers, node_mode.
 * Exports: initAstroConfig()
 * 
 * Depends on: core/utils.js (toast, fetchJSON, withSpinner)
 */

import { toast, fetchJSON, withSpinner } from "./utils.js";

export function initAstroConfig() {
  const lonEl = document.getElementById("astroLon");
  const latEl = document.getElementById("astroLat");
  const altEl = document.getElementById("astroAlt");
  const tzEl  = document.getElementById("astroTz");
  const ayTopEl = document.getElementById("astroAyanamsaTop");

  // NEW fields
  const providerEl = document.getElementById("astroProvider");
  const maxWorkersEl = document.getElementById("astroMaxWorkers");
  const nodeModeEl = document.getElementById("astroNodeMode");

  const locLbl = document.getElementById("astroLocationLabel");
  const tzLbl  = document.getElementById("astroTzLabel");

  const saveBtn  = document.getElementById("astroConfigSave");
  const resetBtn = document.getElementById("astroConfigReset");
  const autoBtn  = document.getElementById("astroAutoDetect");

  const modalAyLbl = document.getElementById("astroAyanamsaModalLabel");


  if (!ayTopEl || !saveBtn || !resetBtn) {
    console.warn("Astro config: required elements not found, skipping init.");
    return;
  }

  const safeNum = (v, fb = 0) => (Number.isFinite(+v) ? +v : fb);

  async function loadAstroConfig() {
    try {
      const data = await fetchJSON("/api/astro/config");
      ayTopEl.value = data.ayanamsa || "lahiri";
      modalAyLbl.textContent = ayTopEl.value;

      // NEW: load provider, max_workers, node_mode if present
      if (providerEl) providerEl.value = data.provider || "skyfield";
      if (maxWorkersEl) maxWorkersEl.value = safeNum(data.max_workers ?? data.ephemeris_max_workers, 1);
      if (nodeModeEl) nodeModeEl.value = data.node_mode || data.ephemeris_node_mode || "mean";

      if (lonEl) lonEl.value = (+data.lon).toFixed(4);
      if (latEl) latEl.value = (+data.lat).toFixed(4);
      if (altEl) altEl.value = data.alt ?? 0;
      if (tzEl)  tzEl.value  = data.tz;

      if (locLbl)
        locLbl.textContent = `${(+data.lon).toFixed(2)} / ${(+data.lat).toFixed(2)}`;
      if (tzLbl)
        tzLbl.textContent = String(data.tz || "").replace("Asia/", "");
    } catch (err) {
      toast("Failed to load Astro configuration", "danger");
      console.error("Astro config load failed:", err);
    }
  }

  async function saveAstroConfig() {
    const payload = {
      lon: safeNum(lonEl?.value, 0),
      lat: safeNum(latEl?.value, 0),
      alt: safeNum(altEl?.value, 0),
      tz:  tzEl?.value || "UTC",
      ayanamsa: ayTopEl?.value || "lahiri",
      // NEW fields included in save payload
      provider: providerEl?.value || "skyfield",
      max_workers: safeNum(maxWorkersEl?.value, 1),
      node_mode: nodeModeEl?.value || "mean",
    };
    await withSpinner(saveBtn, async () => {
      const res = await fetch("/api/astro/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Save failed");
      toast("Astro configuration updated.", "success");
      await loadAstroConfig();
      const modalEl = document.getElementById("astroConfigModal");
      const modalInst = modalEl && bootstrap.Modal.getInstance(modalEl);
      if (modalInst) modalInst.hide();
    });
  }

  async function resetAstroConfig() {
    await withSpinner(resetBtn, async () => {
      const res = await fetch("/api/astro/config/reset", { method: "POST" });
      if (!res.ok) throw new Error("Reset failed");
      toast("Astro configuration reset to defaults.", "warning");
      await loadAstroConfig();
    });
  }

  async function autoDetectLocation() {
    if (!navigator.geolocation) {
      toast("Geolocation not supported in this browser.", "danger");
      return;
    }
    toast("Detecting location...", "info", { duration: 1500 });
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (lonEl) lonEl.value = pos.coords.longitude.toFixed(4);
        if (latEl) latEl.value = pos.coords.latitude.toFixed(4);
        if (altEl) altEl.value = pos.coords.altitude ?? 0;
        try {
          if (tzEl) tzEl.value = Intl.DateTimeFormat().resolvedOptions().timeZone;
        } catch (_) {}
        toast("Detected location and timezone.", "success");
      },
      (err) => toast("Failed to detect location: " + err.message, "warning"),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  async function updateAyanamsa() {
    const newA = ayTopEl.value;
    ayTopEl.disabled = true;
    try {
      const cur = await fetchJSON("/api/astro/config");
      const payload = { ...cur, ayanamsa: newA };
      const res = await fetch("/api/astro/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Failed to update Ayanamsa");
      toast("Ayanamsa updated to " + newA, "success");
      await loadAstroConfig();
    } catch (err) {
      toast("Failed to update Ayanamsa: " + err.message, "danger");
    } finally {
      ayTopEl.disabled = false;
    }
  }

  // --- NEW: update provider (updates server config immediately like updateAyanamsa) ---
  async function updateProvider() {
    if (!providerEl) return;
    const newP = providerEl.value;
    providerEl.disabled = true;
    try {
      const cur = await fetchJSON("/api/astro/config");
      const payload = { ...cur, provider: newP };
      const res = await fetch("/api/astro/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Failed to update provider");
      toast("Ephemeris provider updated to " + newP, "success");
      await loadAstroConfig();
    } catch (err) {
      toast("Failed to update provider: " + err.message, "danger");
      console.error("Provider update failed:", err);
    } finally {
      providerEl.disabled = false;
    }
  }

  // --- NEW: update node mode (updates server config immediately) ---
  async function updateNodeMode() {
    if (!nodeModeEl) return;
    const newMode = nodeModeEl.value;
    nodeModeEl.disabled = true;
    try {
      const cur = await fetchJSON("/api/astro/config");
      const payload = { ...cur, node_mode: newMode };
      const res = await fetch("/api/astro/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Failed to update node mode");
      toast("Node mode updated to " + newMode, "success");
      await loadAstroConfig();
    } catch (err) {
      toast("Failed to update node mode: " + err.message, "danger");
      console.error("Node mode update failed:", err);
    } finally {
      nodeModeEl.disabled = false;
    }
  }

  // --- Event wiring ---
  if (saveBtn)  saveBtn.addEventListener("click", saveAstroConfig);
  if (resetBtn) resetBtn.addEventListener("click", resetAstroConfig);
  if (autoBtn)  autoBtn.addEventListener("click", autoDetectLocation);
  if (ayTopEl)  ayTopEl.addEventListener("change", updateAyanamsa);

  // NEW event listeners for provider / node_mode: update immediately on change (matching your pattern)
  if (providerEl) providerEl.addEventListener("change", updateProvider);
  if (nodeModeEl) nodeModeEl.addEventListener("change", updateNodeMode);

  // --- Initial load ---
  loadAstroConfig();
}


/* ------------------------------------------------------------
   Auto-init if script is loaded directly (not imported)
   ------------------------------------------------------------ */
if (typeof window !== "undefined" && !window.__ASTRO_CONFIG_INIT__) {
  window.__ASTRO_CONFIG_INIT__ = true;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      try {
        initAstroConfig();
      } catch (err) {
        console.error("Astro config init failed:", err);
      }
    });
  } else {
    try {
      initAstroConfig();
    } catch (err) {
      console.error("Astro config init failed:", err);
    }
  }
}
