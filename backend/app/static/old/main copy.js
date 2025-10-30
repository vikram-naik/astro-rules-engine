// ====================================================================
// main.js — streamlined build
// ====================================================================

// ------------------------------------------------------------
// 1. Shared globals and reference loader
// ------------------------------------------------------------
window.REF = { planets: [], relations: [], effects: [] };

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
window.loadReference = loadReference;

window.escapeHtml = (str) => {
  if (!str && str !== 0) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
};

// ------------------------------------------------------------
// 2. Global initialization hook
// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  try {
    await loadReference();
  } catch (_) {}

  if (typeof window.loadSectors === "function") {
    try { await window.loadSectors(); } catch (e) { console.error("loadSectors failed:", e); }
  }
  if (typeof window.loadRules === "function") {
    try { await window.loadRules(); } catch (e) { console.error("loadRules failed:", e); }
  }
});

// ------------------------------------------------------------
// 3. Workbench navigation (sidebar + content panes)
// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const navLinks     = Array.from(document.querySelectorAll("#wbNav a.nav-link"));
  const contentPanes = Array.from(document.querySelectorAll("#workbenchContent > div[id]"));

  function showPaneById(id) {
    contentPanes.forEach((p) => {
      const active = p.id === id.replace("#", "");
      p.classList.toggle("show", active);
      p.classList.toggle("active", active);
      p.style.display = active ? "" : "none";
    });
    navLinks.forEach((a) => a.classList.toggle("active", a.dataset.target === id));
    try { localStorage.setItem("wb:lastView", id); } catch (_) {}
  }

  navLinks.forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      if (a.dataset.target) showPaneById(a.dataset.target);
    })
  );

  const last = localStorage.getItem("wb:lastView") || "#rules";
  showPaneById(last);
  window.wbShowPane = showPaneById;
});

// ------------------------------------------------------------
// 4. Sidebar collapse (fully hides sidebar, persistent)
// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("wbSidebar");
  const toggle = document.getElementById("sidebarToggle");
  const mainContent = document.getElementById("workbenchContent");
  if (!sidebar || !toggle || !mainContent) return;

  function applyCollapsed(collapsed) {
    if (collapsed) {
      sidebar.classList.add("collapsed");
      mainContent.classList.add("expanded");
    } else {
      sidebar.classList.remove("collapsed");
      mainContent.classList.remove("expanded");
    }
  }

  toggle.addEventListener("click", () => {
    const collapsed = !sidebar.classList.contains("collapsed");
    applyCollapsed(collapsed);
    localStorage.setItem("wb:sidebarCollapsed", collapsed ? "1" : "0");
  });

  const stored = localStorage.getItem("wb:sidebarCollapsed") === "1";
  applyCollapsed(stored);
});
