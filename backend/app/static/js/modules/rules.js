/* modules/rules.js
 *
 * Handles Rules table listing, add/edit/delete actions.
 * Clean ES module version.
 */

import { toast, fetchJSON, escapeHtml, withSpinner, useTemplate } from "../core/utils.js";

let rulesTable;
let reloadBtn;

/* ---------- Load & render ---------- */
async function loadRules() {
  if (!rulesTable) {
    rulesTable = document.getElementById("rulesTableBody");
    if (!rulesTable) return; // element not found — safe exit
  }

  try {
    rulesTable.innerHTML =
      `<tr><td colspan="5" class="text-center text-secondary small">Loading...</td></tr>`;
    const rules = await fetchJSON("/api/rules");
    renderRules(rules);
  } catch (err) {
    console.error("Failed to load rules:", err);
    toast("Failed to load rules", "danger");
    rulesTable.innerHTML =
      `<tr><td colspan="5" class="text-center text-danger small">Error loading rules</td></tr>`;
  }
}

/* ---------- Table render ---------- */
function renderRules(rules = []) {
  if (!rulesTable) return;
  if (!Array.isArray(rules) || rules.length === 0) {
    rulesTable.innerHTML =
      `<tr><td colspan="5" data-i18n="rules.noRules" class="text-center text-secondary small">No rules found</td></tr>`;
    return;
  }

  rulesTable.innerHTML = "";

  rules.forEach((r) => {
    const row = useTemplate("rule-row-template");

    row.querySelector(".rule-name").textContent = r.name || "";
    row.querySelector(".rule-description").textContent = r.description || "";
    row.querySelector(".rule-confidence").textContent =
      r.confidence != null ? r.confidence : "";
    row.querySelector(".rule-enabled").textContent = r.enabled ? "✅" : "❌";

    const btnEdit = row.querySelector(".btn-edit-rule");
    const btnDel = row.querySelector(".btn-del-rule");

    btnEdit.dataset.id = r.rule_id;
    btnDel.dataset.id = r.rule_id;

    btnEdit.addEventListener("click", onEditRule);
    btnDel.addEventListener("click", onDeleteRule);

    rulesTable.appendChild(row);
  });
}


/* ---------- CRUD handlers ---------- */
function onEditRule(evt) {
  const id = evt.currentTarget.dataset.id;
  if (!id) return;
  window.location.href = `/ui/rule-editor/${id}`;
}

async function onDeleteRule(evt) {
  const id = evt.currentTarget.dataset.id;
  if (!id) return;
  const btn = evt.currentTarget;
  if (!confirm("Delete this rule?")) return;

  await withSpinner(btn, async () => {
    try {
      const res = await fetch(`/api/rules/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Delete failed");
      toast("Rule deleted", "success");
      await loadRules();
    } catch (err) {
      console.error(err);
      toast("Failed to delete rule", "danger");
    }
  });
}

/* ---------- Init ---------- */
export function initRules() {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initRules);
    return;
  }

  rulesTable = document.getElementById("rulesTableBody");
  reloadBtn = document.getElementById("rulesReloadBtn");
  const addBtn = document.getElementById("btnAddRule");

  if (reloadBtn) reloadBtn.addEventListener("click", loadRules);
  if (addBtn)
    addBtn.addEventListener("click", () => {
      window.location.href = "/ui/rule-editor";
    });

  loadRules();
}
