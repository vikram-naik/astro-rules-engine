// ------------------------------------------------------------
// Astro Configuration Modal + top-bar integration
// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const lonEl = document.getElementById("astroLon");
  const latEl = document.getElementById("astroLat");
  const altEl = document.getElementById("astroAlt");
  const tzEl  = document.getElementById("astroTz");

  const ayTopEl      = document.getElementById("astroAyanamsaTop");
  const locLbl       = document.getElementById("astroLocationLabel");
  const tzLbl        = document.getElementById("astroTzLabel");
  const ayModalLabel = document.getElementById("astroAyanamsaModalLabel");

  const saveBtn  = document.getElementById("astroConfigSave");
  const resetBtn = document.getElementById("astroConfigReset");
  const autoBtn  = document.getElementById("astroAutoDetect");

  const safeNum = (v, fb = 0) => (Number.isFinite(+v) ? +v : fb);

  async function loadAstroConfig() {
    try {
      const res = await fetch("/api/astro/config");
      if (!res.ok) throw new Error("Failed to fetch config");
      const data = await res.json();

      if (ayTopEl) ayTopEl.value = data.ayanamsa || "lahiri";
      if (ayModalLabel)
        ayModalLabel.textContent =
          String(data.ayanamsa || "").replace(/^\w/, (c) => c.toUpperCase()) || "—";

      if (lonEl) lonEl.value = (+data.lon).toFixed(4);
      if (latEl) latEl.value = (+data.lat).toFixed(4);
      if (altEl) altEl.value = data.alt ?? 0;
      if (tzEl)  tzEl.value  = data.tz;

      if (locLbl)
        locLbl.textContent = `${(+data.lon).toFixed(2)} / ${(+data.lat).toFixed(2)}`;
      if (tzLbl)
        tzLbl.textContent = String(data.tz || "").replace("Asia/", "");
    } catch (err) {
      console.error("Failed to load Astro config", err);
    }
  }

  async function saveAstroConfig() {
    const payload = {
      lon: safeNum(lonEl?.value, 0),
      lat: safeNum(latEl?.value, 0),
      alt: safeNum(altEl?.value, 0),
      tz:  tzEl?.value || "UTC",
      ayanamsa: ayTopEl?.value || "lahiri",
    };
    try {
      const res = await fetch("/api/astro/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Save failed");
      toast("Astro configuration updated.", "success");
      await loadAstroConfig();
      const modalEl  = document.getElementById("astroConfigModal");
      const modalInst = modalEl && bootstrap.Modal.getInstance(modalEl);
      if (modalInst) modalInst.hide();
    } catch (err) {
      toast("Failed to save configuration: " + err.message, "danger");
    }
  }

  async function resetAstroConfig() {
    try {
      const res = await fetch("/api/astro/config/reset", { method: "POST" });
      if (!res.ok) throw new Error("Reset failed");
      toast("Astro configuration reset to defaults.", "warning");
      await loadAstroConfig();
    } catch (err) {
      toast("Failed to reset configuration: " + err.message, "danger");
    }
  }

  function toast(message, type = "info") {
    const el = document.createElement("div");
    el.className = "position-fixed top-0 end-0 p-3";
    el.innerHTML = `
      <div class="toast align-items-center text-bg-${type} border-0 show">
        <div class="d-flex">
          <div class="toast-body">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }

  if (autoBtn) {
    autoBtn.addEventListener("click", () => {
      if (!navigator.geolocation) {
        toast("Geolocation is not supported.", "danger");
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          if (lonEl) lonEl.value = pos.coords.longitude.toFixed(4);
          if (latEl) latEl.value = pos.coords.latitude.toFixed(4);
          if (altEl) altEl.value = pos.coords.altitude ?? 0;
          try { if (tzEl) tzEl.value = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (_) {}
          toast("Detected location & timezone.", "info");
        },
        (err) => toast("Failed to detect location: " + err.message, "warning"),
        { enableHighAccuracy: true, timeout: 8000 }
      );
    });
  }

  if (ayTopEl) {
    ayTopEl.addEventListener("change", async () => {
      const newA = ayTopEl.value;
      ayTopEl.disabled = true;
      try {
        const cur = await (await fetch("/api/astro/config")).json();
        const payload = { ...cur, ayanamsa: newA };
        const res = await fetch("/api/astro/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error("Failed to update ayanamsa");
        toast("Ayanamsa updated to " + newA, "success");
        await loadAstroConfig();
      } catch (err) {
        toast("Failed to update ayanamsa: " + err.message, "danger");
        await loadAstroConfig();
      } finally {
        ayTopEl.disabled = false;
      }
    });
  }

  if (saveBtn)  saveBtn.addEventListener("click", saveAstroConfig);
  if (resetBtn) resetBtn.addEventListener("click", resetAstroConfig);

  loadAstroConfig();
});