/* modules/sectors.js
 *
 * Handles Sectors table and modal CRUD operations.
 * Updated to match actual HTML and backend schema (code, name, description).
 */

import { toast, fetchJSON, escapeHtml, withSpinner, useTemplate } from "../core/utils.js";
import { loadSectors as sharedLoadSectors } from "../core/ref_data.js";

/* ---------- Load and render ---------- */
async function loadSectors() {
  const tableBody = document.getElementById("sectorsTableBody");
  if (!tableBody) return;

  tableBody.innerHTML =
    `<tr><td colspan="4" class="text-center text-secondary small">Loading...</td></tr>`;

  try {
    const sectors = await sharedLoadSectors();
    renderSectors(tableBody, sectors);
  } catch (err) {
    console.error("Error loading sectors:", err);
    tableBody.innerHTML =
      `<tr><td colspan="4" class="text-center text-danger small">Error loading sectors</td></tr>`;
    toast("Failed to load sectors", "danger");
  }
}

/* ---------- Render table ---------- */
/* ---------- Render table ---------- */
function renderSectors(tableBody, sectors = []) {
  if (!Array.isArray(sectors) || sectors.length === 0) {
    tableBody.innerHTML =
      `<tr><td colspan="4" class="text-center text-secondary small">No sectors found</td></tr>`;
    return;
  }

  tableBody.innerHTML = "";

  sectors.forEach((s) => {
    const row = useTemplate("sector-row-template")
    row.querySelector(".sector-code").textContent = s.code || "";
    row.querySelector(".sector-name").textContent = s.name || "";
    row.querySelector(".sector-description").textContent = s.description || "";

    const btnEdit = row.querySelector(".btn-edit-sector");
    const btnDel = row.querySelector(".btn-del-sector");

    // retain same data-id semantics
    btnEdit.dataset.id = s.code;
    btnDel.dataset.id = s.code;

    btnEdit.addEventListener("click", onEditSector);
    btnDel.addEventListener("click", onDeleteSector);

    tableBody.appendChild(row);
  });
}


/* ---------- Add / Edit ---------- */
function onAddSector() {
  const modalEl = document.getElementById("sectorModal");
  const modal = new bootstrap.Modal(modalEl);
  const form = document.getElementById("sectorForm");
  const title = document.getElementById("sectorModalTitle");

  form.reset();
  form.dataset.editId = "";
  title.textContent = "Add Sector";
  modal.show();
}

async function onEditSector(e) {
  const id = e.currentTarget.dataset.id;
  if (!id) return;

  const modalEl = document.getElementById("sectorModal");
  const modal = new bootstrap.Modal(modalEl);
  const form = document.getElementById("sectorForm");
  const title = document.getElementById("sectorModalTitle");

  title.textContent = "Edit Sector";
  form.reset();

  try {
    const s = await fetchJSON(`/api/sectors/${id}`);
    document.getElementById("sector_id").value = s.id
    document.getElementById("sector_code").value = s.code || "";
    document.getElementById("sector_name").value = s.name || "";
    document.getElementById("sector_description").value = s.description || "";

    modal.show();
  } catch (err) {
    console.error(err);
    toast("Failed to load sector", "danger");
  }
}

/* ---------- Delete ---------- */
async function onDeleteSector(e) {
  const id = e.currentTarget.dataset.id;
  if (!id) return;
  if (!confirm("Delete this sector?")) return;

  await withSpinner(e.currentTarget, async () => {
    try {
      const res = await fetch(`/api/sectors/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete sector");
      toast("Sector deleted", "success");
      await sharedLoadSectors(true);
      await loadSectors();
    } catch (err) {
      console.error(err);
      toast("Failed to delete sector", "danger");
    }
  });
}

/* ---------- Save ---------- */
async function onSaveSector(e) {
  e.preventDefault();

  const form = e.target;
  const editId = form.sector_id.value.trim();
  console.log(editId)

  const code = form.sector_code.value.trim();
  const name = form.sector_name.value.trim();
  const description = form.sector_description.value.trim();

  if (!code || !name) {
    toast("Code and Name are required", "warning");
    return;
  }

  const payload = { code, name, description };

  await withSpinner(form.querySelector("button[type='submit']"), async () => {
    try {
      const url = editId ? `/api/sectors/${editId}` : "/api/sectors";
      const method = editId ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to save sector");

      toast(editId ? "Sector updated" : "Sector added", "success");
      document.activeElement?.blur();
      const modalEl = document.getElementById("sectorModal");
      const modal = bootstrap.Modal.getInstance(modalEl);
      modal.hide();

      await sharedLoadSectors(true);
      await loadSectors();
    } catch (err) {
      console.error(err);
      toast("Failed to save sector", "danger");
    }
  });
}

/* ---------- Init ---------- */
export function initSectors() {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSectors);
    return;
  }

  const addBtn = document.getElementById("btnAddSector");
  const form = document.getElementById("sectorForm");

  if (addBtn) addBtn.addEventListener("click", onAddSector);
  if (form) form.addEventListener("submit", onSaveSector);

  loadSectors();
}
