/* core/utils.js
 *
 * Shared helper utilities used across modules.
 *
 * Exports:
 *   export function escapeHtml(str)
 *   export async function fetchJSON(url, opts)
 *   export function toast(message, type = "info", opts = {})
 *   export function withSpinner(targetBtn, asyncFn) - helper to run async work with spinner UI
 *
 * Also sets window.escapeHtml and window.toast for backward compatibility so existing scripts
 * that reference them directly continue to work until you convert those scripts to imports.
 *
 * No assumptions made about server endpoints; this is purely UI helper code.
 */

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  // keep typesafe and small
  const s = String(str);
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function fetchJSON(url, opts = {}) {
  const cfg = Object.assign({ credentials: "same-origin" }, opts);
  const res = await fetch(url, cfg);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(
      `fetchJSON ${res.status} ${res.statusText}${text ? ": " + text : ""}`
    );
    err.status = res.status;
    err.body = text;
    throw err;
  }
  // try parse json; let exceptions bubble
  return await res.json();
}

/* Toast helper
 *
 * message: string or DOM-ready string
 * type: one of "info", "success", "warning", "danger" — maps to Bootstrap text-bg-{type}
 * opts: { duration: ms (default 3000), containerClass: string } — optional
 */
function toast(message, type = "info", opts = {}) {
  const { duration = 3000, containerClass = "" } = opts;
  const wrapper = document.createElement("div");
  wrapper.className = `position-fixed top-0 end-0 p-3 ${containerClass}`;
  wrapper.style.zIndex = 2000;

  // sanitize simple text via escapeHtml for safety
  const body = typeof message === "string" ? escapeHtml(message) : message;

  wrapper.innerHTML = `
    <div class="toast align-items-center text-bg-${type} border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body">${body}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>`;

  document.body.appendChild(wrapper);

  // remove after duration (allow manual close via data-bs-dismiss)
  const t = setTimeout(() => {
    wrapper.remove();
  }, duration);

  // clean up if user closes manually
  wrapper.addEventListener("click", (e) => {
    // if user clicked close button or container, remove quickly
    if (e.target.closest(".btn-close") || e.target === wrapper) {
      clearTimeout(t);
      wrapper.remove();
    }
  });

  return wrapper;
}

/* withSpinner helper
 *
 * Usage:
 *   await withSpinner(buttonElement, async () => {
 *     // do async work
 *   });
 *
 * It will:
 *  - disable the button,
 *  - append a small spinner,
 *  - run the async function,
 *  - restore the button state and remove spinner,
 *  - rethrow any error.
 */
async function withSpinner(targetBtn, asyncFn) {
  if (!targetBtn || typeof asyncFn !== "function") {
    return await asyncFn(); // no spinner if no button provided
  }

  const spinner = document.createElement("span");
  spinner.className = "spinner-border spinner-border-sm ms-2 text-light";
  spinner.setAttribute("role", "status");
  spinner.setAttribute("aria-hidden", "true");

  try {
    targetBtn.disabled = true;
    targetBtn.appendChild(spinner);
    const result = await asyncFn();
    return result;
  } finally {
    try {
      spinner.remove();
    } catch (_) {}
    targetBtn.disabled = false;
  }
}

function useTemplate(id) {
  const tpl = document.getElementById(id);
  if (!tpl) throw new Error(`Template '${id}' not found`);
  return tpl.content.cloneNode(true);
}

function showOverlay(el, show = true) {
  if (!el) return;
  // prefer class toggle for transitions and less brittle layout changes
  if (show) {
    el.classList.add("visible");
    el.setAttribute("aria-hidden", "false");
  } else {
    el.classList.remove("visible");
    el.setAttribute("aria-hidden", "true");
  }
}


/* Backwards compatibility: set window.* so current non-module callers work immediately.
   This avoids having to edit all files before we migrate them. We will remove these
   assignments later, step-by-step, as modules are converted to imports.
*/
if (typeof window !== "undefined") {
  window.escapeHtml = escapeHtml;
  window.fetchJSON = fetchJSON;
  window.toast = toast;
  window.withSpinner = withSpinner;
  window.showOverlay = showOverlay;
}

/* Exports for module consumers */
export { escapeHtml, fetchJSON, toast, withSpinner, useTemplate, showOverlay };
