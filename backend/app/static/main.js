// main.js (patched)
// Shared globals and references
window.REF = { planets: [], relations: [], effects: [] };

// Helper functions
async function loadReference() {
  try {
    const r = await fetch("/api/reference/");
    window.REF = await r.json();
    return window.REF;
  } catch (err) {
    console.error("reference load fail", err);
    throw err;
  }
}

// expose globally so other modules can call it
window.loadReference = loadReference;

window.escapeHtml = function (str) {
  if (!str && str !== 0) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
};

// Application initialization
document.addEventListener("DOMContentLoaded", async () => {
  // initialize REF for pages that depend on it
  try {
    await loadReference();
  } catch (e) {
    // already logged in loadReference
  }

  // If page defines `loadSectors` / `loadRules`, call them but guard
  if (typeof window.loadSectors === "function") {
    try {
      await window.loadSectors();
    } catch (e) {
      console.error("loadSectors failed:", e);
    }
  }
  if (typeof window.loadRules === "function") {
    try {
      await window.loadRules();
    } catch (e) {
      console.error("loadRules failed:", e);
    }
  }
});

// =============================
// Astro Configuration (UX Enhanced)
// =============================
document.addEventListener("DOMContentLoaded", () => {
  // modal inputs
  const lonEl = document.getElementById('astroLon');
  const latEl = document.getElementById('astroLat');
  const altEl = document.getElementById('astroAlt');
  const tzEl  = document.getElementById('astroTz');

  // top-level controls / labels
  const ayTopEl = document.getElementById('astroAyanamsaTop'); // top select
  const locLbl = document.getElementById('astroLocationLabel');
  const tzLbl  = document.getElementById('astroTzLabel');
  const ayModalLabel = document.getElementById('astroAyanamsaModalLabel'); // read-only in modal

  // modal action buttons
  const saveBtn = document.getElementById('astroConfigSave');
  const resetBtn = document.getElementById('astroConfigReset');
  const autoBtn = document.getElementById('astroAutoDetect');

  // small helper: safe number parse
  function safeNum(v, fallback = 0) {
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : fallback;
  }

  async function loadAstroConfig() {
    try {
      const res = await fetch('/api/astro/config');
      if (!res.ok) throw new Error('Failed to fetch config');
      const data = await res.json();

      // populate top select (ayanamsa) first
      if (ayTopEl) {
        ayTopEl.value = data.ayanamsa || 'lahiri';
      }
      // update read-only modal label if present
      if (ayModalLabel) {
        const pretty = String(data.ayanamsa || '').replace(/^\w/, c => c.toUpperCase());
        ayModalLabel.textContent = pretty || '—';
      }

      // fill modal fields (if present)
      if (lonEl) lonEl.value = (+data.lon).toFixed(4);
      if (latEl) latEl.value = (+data.lat).toFixed(4);
      if (altEl) altEl.value = (data.alt ?? 0);
      if (tzEl)  tzEl.value  = data.tz;

      // update compact location and tz labels
      if (locLbl) locLbl.textContent = `${(+data.lon).toFixed(2)} / ${(+data.lat).toFixed(2)}`;
      if (tzLbl)  tzLbl.textContent  = String(data.tz || '').replace('Asia/', '');
    } catch (err) {
      console.error('Failed to load Astro config', err);
    }
  }

  // Save from modal -> posts full payload (including ayanamsa from top select)
  async function saveAstroConfig() {
    const payload = {
      lon: safeNum(lonEl?.value, 0),
      lat: safeNum(latEl?.value, 0),
      alt: safeNum(altEl?.value, 0),
      tz: tzEl?.value || 'UTC',
      // take ayanamsa from top select so modal doesn't need its own control
      ayanamsa: ayTopEl?.value || 'lahiri'
    };
    try {
      const res = await fetch('/api/astro/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Save failed');
      toast("Astro configuration updated.", "success");
      await loadAstroConfig();
      // close modal if open
      const modalEl = document.getElementById('astroConfigModal');
      const modalInst = modalEl && bootstrap.Modal.getInstance(modalEl);
      if (modalInst) modalInst.hide();
    } catch (err) {
      toast("Failed to save configuration: " + err.message, "danger");
    }
  }

  // Reset to defaults on backend (reads .env defaults)
  async function resetAstroConfig() {
    try {
      const res = await fetch('/api/astro/config/reset', { method: 'POST' });
      if (!res.ok) throw new Error('Reset failed');
      toast("Astro configuration reset to defaults.", "warning");
      await loadAstroConfig();
    } catch (err) {
      toast("Failed to reset configuration: " + err.message, "danger");
    }
  }

  // show small toast
  function toast(message, type = "info") {
    const el = document.createElement("div");
    el.className = "position-fixed top-0 end-0 p-3";
    el.innerHTML =
      `<div class="toast align-items-center text-bg-${type} border-0 show">
         <div class="d-flex">
           <div class="toast-body">${message}</div>
           <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
         </div>
       </div>`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }

  // Auto-detect (on-demand only; populates modal fields, doesn't auto-save)
  if (autoBtn) {
    autoBtn.addEventListener('click', () => {
      if (!navigator.geolocation) {
        toast("Geolocation is not supported by your browser.", "danger");
        return;
      }
      navigator.geolocation.getCurrentPosition(
        pos => {
          if (lonEl) lonEl.value = pos.coords.longitude.toFixed(4);
          if (latEl) latEl.value = pos.coords.latitude.toFixed(4);
          if (altEl) altEl.value = (pos.coords.altitude ?? 0);
          try {
            if (tzEl) tzEl.value = Intl.DateTimeFormat().resolvedOptions().timeZone;
          } catch (_) {}
          toast("Detected your location and timezone.", "info");
        },
        err => toast("Failed to detect location: " + (err.message || err), "warning"),
        { enableHighAccuracy: true, timeout: 8000 }
      );
    });
  }

  // Top ayanamsa change: apply immediately by posting full payload (preserving other values)
  if (ayTopEl) {
    ayTopEl.addEventListener('change', async () => {
      const newA = ayTopEl.value;
      ayTopEl.disabled = true;
      try {
        // fetch current server config so we preserve other fields
        const curRes = await fetch('/api/astro/config');
        if (!curRes.ok) throw new Error('Failed to read current config');
        const current = await curRes.json();

        const payload = {
          lon: safeNum(current.lon, 0),
          lat: safeNum(current.lat, 0),
          alt: safeNum(current.alt ?? 0, 0),
          tz: current.tz || 'UTC',
          ayanamsa: newA
        };

        const res = await fetch('/api/astro/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('Failed to update ayanamsa');

        await loadAstroConfig();
        toast('Ayanamsa updated to ' + newA, 'success');
      } catch (err) {
        console.error('Error updating ayanamsa', err);
        toast('Failed to update ayanamsa: ' + (err.message || err), 'danger');
        // reload the current server value to keep UI consistent
        await loadAstroConfig();
      } finally {
        ayTopEl.disabled = false;
      }
    });
  }

  if (saveBtn) saveBtn.addEventListener('click', saveAstroConfig);
  if (resetBtn) resetBtn.addEventListener('click', resetAstroConfig);

  // Initial load
  loadAstroConfig();
});
