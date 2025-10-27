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
