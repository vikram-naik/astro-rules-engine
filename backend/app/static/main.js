(() => {
  // ==============================
  // Shared globals and references
  // ==============================
  window.REF = { planets: [], relations: [], effects: [] };

  // ===============
  // Helper functions
  // ===============
  async function loadReference() {
    try {
      const r = await fetch("/api/reference/");
      window.REF = await r.json();
    } catch (err) {
      console.error("reference load fail", err);
    }
  }

  window.escapeHtml = function (str) {
    if (!str && str !== 0) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };

  // ========================
  // Application initialization
  // ========================
  document.addEventListener("DOMContentLoaded", async () => {
    await loadReference();
    if (window.loadSectors) await window.loadSectors();
    if (window.loadRules) await window.loadRules();
  });
})();
