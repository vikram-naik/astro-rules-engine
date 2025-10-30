// =============================
// rules.js (Refactored for Full-Page Rule Editor)
// =============================

const rulesBody = document.getElementById("rulesBody");
const btnAddRule = document.getElementById("btnAddRule");

// Load all rules from API
async function loadRules() {
  console.log("loadRules")
  rulesBody.innerHTML = '<tr><td colspan="5" class="text-muted">Loading…</td></tr>';
  try {
    const resp = await fetch("/api/rules/");
    const data = await resp.json();
    console.log("loadRules", data)
    renderRules(data);
  } catch (err) {
    console.error(err);
    rulesBody.innerHTML = '<tr><td colspan="5" class="text-danger">Failed to load rules</td></tr>';
  }
}

// Render rules table
function renderRules(rules) {
  if (!rules || rules.length === 0) {
    rulesBody.innerHTML = '<tr><td colspan="5" class="text-muted">No rules found</td></tr>';
    return;
  }

  rulesBody.innerHTML = "";
  rules.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(r.name)}</td>
      <td>${escapeHtml(r.description || "")}</td>
      <td>${(r.confidence || 0).toFixed(2)}</td>
      <td>${r.enabled ? "✅" : "❌"}</td>
      <td>
        <button class="btn btn-sm btn-outline-light btn-edit" data-id="${r.rule_id}" title="Edit">
          <i class="bi bi-pencil"></i>
        </button>
        <button class="btn btn-sm btn-outline-danger btn-del" data-id="${r.rule_id}" title="Delete">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    `;
    rulesBody.appendChild(tr);
  });

  // Bind delete and edit buttons
  document.querySelectorAll(".btn-del").forEach((b) => b.addEventListener("click", onDeleteRule));
  document.querySelectorAll(".btn-edit").forEach((b) => b.addEventListener("click", onEditRule));
}

// Delete rule handler
async function onDeleteRule(evt) {
  const id = evt.currentTarget.dataset.id;
  if (!confirm("Delete rule?")) return;
  try {
    const resp = await fetch(`/api/rules/${id}`, { method: "DELETE" });
    if (!resp.ok) throw new Error("delete failed");
    await loadRules();
  } catch (err) {
    console.error(err);
    alert("Failed to delete rule");
  }
}

// Redirect Add Rule button to new rule editor
btnAddRule.addEventListener("click", () => {
  window.location.href = "/ui/rule-editor";
});

// Edit rule handler
function onEditRule(evt) {
  const id = evt.currentTarget.dataset.id;
  if (!id) return;
  window.location.href = `/ui/rule-editor/${id}`;
}

// Expose globally for tab initialization
window.loadRules = loadRules;