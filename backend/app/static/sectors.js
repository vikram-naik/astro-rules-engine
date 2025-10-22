
const sectorsBody = document.getElementById("sectorsBody");
const btnAddSector = document.getElementById("btnAddSector");

// Modals
const sectorModalEl = document.getElementById("sectorModal");
const sectorModal = new bootstrap.Modal(sectorModalEl);

// Forms
const sectorForm = document.getElementById("sectorForm");


async function loadSectors() {
    sectorsBody.innerHTML = '<tr><td colspan="4" class="text-muted">Loading…</td></tr>';
    try {
        const resp = await fetch("/api/sectors/");
        const rows = await resp.json();
        window.SECTORS = rows;  // ✅ cache globally
        if (!rows || rows.length === 0) {
            sectorsBody.innerHTML = '<tr><td colspan="4" class="text-muted">No sectors</td></tr>';
            return;
        }
        sectorsBody.innerHTML = "";
        rows.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
          <td>${escapeHtml(s.code)}</td>
          <td>${escapeHtml(s.name)}</td>
          <td>${escapeHtml(s.description || "")}</td>
          <td>
            <button class="btn btn-sm btn-outline-light me-1 btn-edit-sector" data-id="${s.id}">Edit</button>
            <button class="btn btn-sm btn-outline-danger btn-del-sector" data-id="${s.id}">Delete</button>
          </td>
        `;
            sectorsBody.appendChild(tr);
        });
        document.querySelectorAll(".btn-edit-sector").forEach(b => b.addEventListener("click", onEditSector));
        document.querySelectorAll(".btn-del-sector").forEach(b => b.addEventListener("click", onDeleteSector));
    } catch (err) {
        console.error(err);
        sectorsBody.innerHTML = '<tr><td colspan="4" class="text-danger">Failed to load sectors</td></tr>';
    }
}

btnAddSector.addEventListener("click", () => openSectorModal());

function openSectorModal(sector = null) {
    document.getElementById("sectorForm").reset();
    document.getElementById("sector_id").value = sector ? sector.id : "";
    document.getElementById("sector_code").value = sector ? sector.code : "";
    document.getElementById("sector_name").value = sector ? sector.name : "";
    document.getElementById("sector_description").value = sector ? sector.description : "";
    document.getElementById("sectorModalTitle").textContent = sector ? "Edit Sector" : "Add Sector";
    sectorModal.show();
}

async function onEditSector(evt) {
    const id = evt.currentTarget.dataset.id;
    try {
        const resp = await fetch(`/api/sectors/`);
        const all = await resp.json();
        const s = all.find(x => String(x.id) === String(id));
        openSectorModal(s);
    } catch (err) {
        console.error(err);
        alert("Failed to load sector");
    }
}

async function onDeleteSector(evt) {
    const id = evt.currentTarget.dataset.id;
    if (!confirm("Delete sector?")) return;
    try {
        const resp = await fetch(`/api/sectors/${id}`, { method: "DELETE" });
        if (!resp.ok) throw new Error("delete failed");
        await loadSectors();
    } catch (err) {
        console.error(err);
        alert("Failed to delete sector");
    }
}

sectorForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("sector_id").value;
    const payload = {
        code: document.getElementById("sector_code").value,
        name: document.getElementById("sector_name").value,
        description: document.getElementById("sector_description").value,
    };
    try {
        let resp;
        if (id) {
            resp = await fetch(`/api/sectors/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        } else {
            resp = await fetch(`/api/sectors/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        }
        if (!resp.ok) throw new Error("save failed");
        sectorModal.hide();
        await loadSectors();
    } catch (err) {
        console.error(err);
        alert("Failed to save sector");
    }
});