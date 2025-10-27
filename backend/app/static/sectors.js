// =============================
// sectors.js (final shared version)
// =============================

async function loadSectors() {
  const sectorsBody = document.getElementById("sectorsBody");
  try {
    const resp = await fetch("/api/sectors/");
    const rows = await resp.json();
    window.SECTORS = rows || [];

    // If there's no table (e.g., in rule_editor.html), just return the data
    if (!sectorsBody) return window.SECTORS;

    // Render table if present
    if (!rows || rows.length === 0) {
      sectorsBody.innerHTML = '<tr><td colspan="4" class="text-muted">No sectors</td></tr>';
      return window.SECTORS;
    }

    sectorsBody.innerHTML = "";
    rows.forEach((s) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(s.code)}</td>
        <td>${escapeHtml(s.name)}</td>
        <td>${escapeHtml(s.description || "")}</td>
        <td>
          <button class="btn btn-sm btn-outline-light me-1 btn-edit-sector" data-id="${s.code}">Edit</button>
          <button class="btn btn-sm btn-outline-danger btn-del-sector" data-id="${s.code}">Delete</button>
        </td>
      `;
      sectorsBody.appendChild(tr);
    });

    document.querySelectorAll(".btn-edit-sector").forEach((b) =>
      b.addEventListener("click", onEditSector)
    );
    document.querySelectorAll(".btn-del-sector").forEach((b) =>
      b.addEventListener("click", onDeleteSector)
    );

    return window.SECTORS;
  } catch (err) {
    console.error("[loadSectors] failed:", err);
    if (sectorsBody)
      sectorsBody.innerHTML = '<tr><td colspan="4" class="text-danger">Failed to load sectors</td></tr>';
    window.SECTORS = [];
    return [];
  }
}

// =====================================================
// Handlers (only run if modal is available on page)
// =====================================================

function getSectorModalInstance() {
  const el = document.getElementById("sectorModal");
  if (!el) return null;
  if (!el._bsInstance) el._bsInstance = new bootstrap.Modal(el);
  return el._bsInstance;
}

async function onEditSector(evt) {
  const code = evt.currentTarget.dataset.id;
  const modal = getSectorModalInstance();
  if (!modal) return; // not available in rule editor

  try {
    const resp = await fetch(`/api/sectors/${code}`);
    if (!resp.ok) throw new Error("Failed to load sector details");
    const s = await resp.json();

    const title = document.getElementById("sectorModalTitle");
    const idField = document.getElementById("sector_id");
    const codeField = document.getElementById("sector_code");
    const nameField = document.getElementById("sector_name");
    const descField = document.getElementById("sector_description");

    if (title) title.textContent = "Edit Sector";
    if (idField) idField.value = s.id;
    if (codeField) codeField.value = s.code || "";
    if (nameField) nameField.value = s.name || "";
    if (descField) descField.value = s.description || "";

    modal.show();
  } catch (err) {
    console.error("[onEditSector] failed:", err);
    alert("Failed to load sector for editing");
  }
}

async function onDeleteSector(evt) {
  const id = evt.currentTarget.dataset.id;
  if (!confirm("Delete this sector?")) return;

  try {
    const resp = await fetch(`/api/sectors/${id}`, { method: "DELETE" });
    if (!resp.ok) throw new Error("Delete failed");
    await loadSectors();
  } catch (err) {
    console.error("[onDeleteSector] failed:", err);
    alert("Failed to delete sector");
  }
}

// =====================================================
// Sector Form Handling
// =====================================================
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("sectorForm");
  const modal = getSectorModalInstance();
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("sector_id").value;
    const code = document.getElementById("sector_code").value.trim();
    const name = document.getElementById("sector_name").value.trim();
    const description = document.getElementById("sector_description").value.trim();

    try {
      const payload = { code, name, description };
      const resp = await fetch(`/api/sectors/${id || ""}`, {
        method: id ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error("Save failed");

      await loadSectors();
      if (modal) modal.hide();
    } catch (err) {
      console.error("[sectorForm submit] failed:", err);
      alert("Failed to save sector");
    }
  });

  const btnAddSector = document.getElementById("btnAddSector");
  if (btnAddSector) {
    btnAddSector.addEventListener("click", () => {
      const title = document.getElementById("sectorModalTitle");
      const idField = document.getElementById("sector_id");
      const form = document.getElementById("sectorForm");
      if (title) title.textContent = "Add Sector";
      if (idField) idField.value = "";
      if (form) form.reset();
      const modal = getSectorModalInstance();
      if (modal) modal.show();
    });
  }
});

// expose globally
window.loadSectors = loadSectors;
