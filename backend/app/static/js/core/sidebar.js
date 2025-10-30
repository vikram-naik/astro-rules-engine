/* core/sidebar.js
 *
 * Handles sidebar collapse/expand and pane navigation for the Workbench UI.
 * 
 * Exports:
 *   initSidebar() – sets up event listeners
 *
 * Also assigns window.wbShowPane for backward compatibility until all scripts
 * are converted to modules.
 */

import { toast } from "./utils.js";

/** Toggle sidebar collapsed/expanded */
function applyCollapsed(collapsed) {
  const sidebar = document.getElementById("wbSidebar");
  const content = document.getElementById("workbenchContent");
  if (!sidebar || !content) return;

  if (collapsed) {
    sidebar.classList.add("collapsed");
    content.classList.add("expanded");
  } else {
    sidebar.classList.remove("collapsed");
    content.classList.remove("expanded");
  }
}

/** Show a content pane by id (e.g. "#rules") */
function showPaneById(id) {
  const contentPanes = document.querySelectorAll("#workbenchContent > div[id]");
  const navLinks = document.querySelectorAll("#wbNav a.nav-link");
  const targetId = id.startsWith("#") ? id.substring(1) : id;

  contentPanes.forEach((p) => {
    const active = p.id === targetId;
    p.classList.toggle("show", active);
    p.classList.toggle("active", active);
    p.style.display = active ? "" : "none";
  });

  navLinks.forEach((a) =>
    a.classList.toggle("active", a.dataset.target === `#${targetId}`)
  );

  try {
    localStorage.setItem("wb:lastView", `#${targetId}`);
  } catch (_) {}
}

/** Initialize sidebar logic */
function initSidebar() {
  const sidebar = document.getElementById("wbSidebar");
  const toggle = document.getElementById("sidebarToggle");
  const content = document.getElementById("workbenchContent");
  const navLinks = document.querySelectorAll("#wbNav a.nav-link");

  if (!sidebar || !toggle || !content) {
    console.warn("Sidebar elements not found – sidebar disabled.");
    return;
  }

  // --- Collapse toggle handling ---
  toggle.addEventListener("click", () => {
    const collapsed = !sidebar.classList.contains("collapsed");
    applyCollapsed(collapsed);
    try {
      localStorage.setItem("wb:sidebarCollapsed", collapsed ? "1" : "0");
    } catch (_) {}
  });

  // --- Nav link handling ---
  navLinks.forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      if (a.dataset.target) showPaneById(a.dataset.target);
    })
  );

  // --- Restore persisted states ---
  const collapsed = localStorage.getItem("wb:sidebarCollapsed") === "1";
  applyCollapsed(collapsed);

  const last = localStorage.getItem("wb:lastView") || "#rules";
  showPaneById(last);

  // --- Expose legacy helper ---
  window.wbShowPane = showPaneById;

  // --- Optional feedback toast (commented out) ---
//   toast("Sidebar initialized", "info", { duration: 1000 });
}

/* Export module API */
export { initSidebar };
