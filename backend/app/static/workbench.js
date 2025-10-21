// app/static/workbench.js
// Minimal AJAX client for Workbench (vanilla JS)

(() => {
  const rulesBody = document.getElementById("rulesBody");
  const sectorsBody = document.getElementById("sectorsBody");
  const btnAddRule = document.getElementById("btnAddRule");
  const btnAddSector = document.getElementById("btnAddSector");

  // Modals
  const ruleModalEl = document.getElementById("ruleModal");
  const ruleModal = new bootstrap.Modal(ruleModalEl);
  const sectorModalEl = document.getElementById("sectorModal");
  const sectorModal = new bootstrap.Modal(sectorModalEl);

  // Forms
  const ruleForm = document.getElementById("ruleForm");
  const sectorForm = document.getElementById("sectorForm");

  // Correlation
  const btnRunCorr = document.getElementById("btnRunCorr");
  const corrResults = document.getElementById("corrResults");

  // Initialize
  let REF = {planets:[], relations:[], effects:[]};

  async function loadReference() {
    try {
      const r = await fetch("/api/reference/");
      REF = await r.json();
    } catch (err) { console.error("reference load fail", err); }
  }

  document.addEventListener("DOMContentLoaded", async () => {
    await loadReference();
    await loadSectors();
    await loadRules();
  });


  // ---------------------- RULES ----------------------
  function populateSelectOptions() {
    const planetSel = document.getElementById("rule_planet");
    const targetSel = document.getElementById("rule_target");
    const relSel = document.getElementById("rule_relation");
    const effectSel = document.getElementById("rule_effect");
    const sectorSel = document.getElementById("rule_sector");

    const fill = (el, arr, getValue, getLabel) => {
      el.innerHTML = '<option value="" selected disabled>-- Select --</option>';
      if (!arr || arr.length === 0) return;
      el.innerHTML += arr
        .map(item => {
          const val = getValue(item);
          const label = getLabel(item);
          return `<option value="${val}">${label}</option>`;
        })
        .join("");
    };

    // Planets (both main and target)
    fill(planetSel, REF.planets, x => x.key, x => x.label);
    fill(targetSel, REF.planets, x => x.key, x => x.label);

    // Relations & Effects
    fill(relSel, REF.relations, x => x.key, x => x.label);
    fill(effectSel, REF.effects, x => x.key, x => x.label);

    // Sectors from DB
    fill(sectorSel, window.SECTORS || [], s => s.id, s => `${s.name} (${s.code})`);
  }


  async function loadRules() {
    rulesBody.innerHTML = '<tr><td colspan="5" class="text-muted">Loading…</td></tr>';
    try {
      const resp = await fetch("/api/rules/");
      const data = await resp.json();
      renderRules(data);
    } catch (err) {
      console.error(err);
      rulesBody.innerHTML = '<tr><td colspan="5" class="text-danger">Failed to load rules</td></tr>';
    }
  }

  function renderRules(rules) {
    if (!rules || rules.length === 0) {
      rulesBody.innerHTML = '<tr><td colspan="5" class="text-muted">No rules found</td></tr>';
      return;
    }
    rulesBody.innerHTML = "";
    rules.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(r.name)}</td>
        <td>${escapeHtml(r.description || "")}</td>
        <td>${(r.confidence||0).toFixed(2)}</td>
        <td>${r.enabled ? "Yes" : "No"}</td>
        <td>
          <button class="btn btn-sm btn-outline-light me-1 btn-edit" data-id="${r.rule_id}">Edit</button>
          <button class="btn btn-sm btn-outline-danger btn-del" data-id="${r.rule_id}">Delete</button>
        </td>
      `;
      rulesBody.appendChild(tr);
    });

    // attach handlers
    document.querySelectorAll(".btn-edit").forEach(b => b.addEventListener("click", onEditRule));
    document.querySelectorAll(".btn-del").forEach(b => b.addEventListener("click", onDeleteRule));
  }

  btnAddRule.addEventListener("click", () => {
    openRuleModal();
  });

  async function openRuleModal(rule = null) {
    // Ensure we have reference data + sectors loaded
    if (!REF.planets.length || !REF.relations.length) await loadReference();
    if (!window.SECTORS || !window.SECTORS.length) await loadSectors();
    populateSelectOptions();

    // Reset all form fields
    ruleForm.reset();
    document.getElementById("rule_id").value = rule ? rule.rule_id : "";
    document.getElementById("rule_name").value = rule ? rule.name : "";
    document.getElementById("rule_description").value = rule ? rule.description : "";
    document.getElementById("rule_confidence").value = rule ? rule.confidence : 0.8;
    document.getElementById("rule_enabled").checked = rule ? rule.enabled : true;
    document.getElementById("rule_weight").value = rule?.outcomes?.[0]?.weight || 1.0;

    const planetSel = document.getElementById("rule_planet");
    const relSel = document.getElementById("rule_relation");
    const targetSel = document.getElementById("rule_target");
    const sectorSel = document.getElementById("rule_sector");
    const effectSel = document.getElementById("rule_effect");

    // Always start with empty defaults ("-- Select --")
    [planetSel, relSel, targetSel, sectorSel, effectSel].forEach(el => {
      if (el) el.value = "";
    });

    // 🧠 If edit mode — preselect correct dropdown values
    if (rule) {
      console.log(rule)
      const cond = rule.conditions?.[0] || {};
      const out = rule.outcomes?.[0] || {};

      // Planets — backend stores as string labels like "Sun"
      if (cond.planet) {
        const match = REF.planets.find(p => p.key === cond.planet || p.label === cond.planet);
        if (match) planetSel.value = match.key;
      }

      // Relation — stored as enum key like "in_nakshatra_owned_by"
      if (cond.relation) relSel.value = cond.relation;

      // Target — same as planet
      if (cond.target) {
        const match = REF.planets.find(p => p.key === cond.target || p.label === cond.target);
        if (match) targetSel.value = match.key;
      }

      // Sector — stored as code
      if (out.sector_id) {
        const match = (window.SECTORS || []).find(s => s.id === out.sector_id);
        if (match) sectorSel.value = match.id;
      }

      // Effect — stored as enum key ("Bullish", "Bearish", etc.)
      if (out.effect) effectSel.value = out.effect;
    }

    document.getElementById("ruleModalTitle").textContent = rule ? "Edit Rule" : "Add Rule";
    ruleModal.show();
  }

  async function onEditRule(evt) {
    const id = evt.currentTarget.dataset.id;
    try {
      const resp = await fetch(`/api/rules/${id}`);
      if (!resp.ok) throw new Error("Failed to fetch rule");
      const r = await resp.json();
      console.log(r)
      openRuleModal(r);
      document.getElementById("rule_id").value = r.rule_id;
    } catch (err) {
      console.error(err);
      alert("Failed to load rule");
    }
  }

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

  ruleForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const id = document.getElementById("rule_id").value;
    const ruleName = document.getElementById("rule_name").value.trim();   // ✅ define properly
    const description = document.getElementById("rule_description").value.trim();
    const confidence = parseFloat(document.getElementById("rule_confidence").value || 1.0);
    const enabled = document.getElementById("rule_enabled").checked;

    const payload = {
      name: ruleName,
      description,
      confidence,
      enabled,
      conditions: [
        {
          planet: document.getElementById("rule_planet").value || "",
          relation: document.getElementById("rule_relation").value || "",
          target: document.getElementById("rule_target").value || ""
        }
      ],
      outcomes: [
        {
          sector_id: document.getElementById("rule_sector").value || "",
          effect: document.getElementById("rule_effect").value || "",
          weight: parseFloat(document.getElementById("rule_weight").value || 1.0)
        }
      ]
    };

    try {
      let resp;
      if (id) {
        resp = await fetch(`/api/rules/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        resp = await fetch(`/api/rules/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "unexpected" }));
        throw new Error(err.detail || "Save failed");
      }

      ruleModal.hide();
      await loadRules();
    } catch (err) {
      console.error(err);
      alert("Failed to save rule: " + err.message);
    }
  });


  // ---------------------- SECTORS ----------------------
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

  // ---------------------- CORRELATION ----------------------
  btnRunCorr.addEventListener("click", async (e) => {
    e.preventDefault();
    corrResults.innerHTML = '<div class="text-muted">Running…</div>';

    const start = document.getElementById("corrStart").value;
    const end = document.getElementById("corrEnd").value;
    const ticker = document.getElementById("corrTicker").value || "^GSPC";
    const look = (document.getElementById("corrLookahead").value || "1,3,5").split(",").map(s => parseInt(s.trim())).filter(Boolean);

    const payload = {
      start_date: start,
      end_date: end,
      ticker: ticker,
      lookahead_days: look
    };

    try {
      const resp = await fetch("/correlation/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!resp.ok) {
        const err = await resp.json().catch(()=>({detail:"error"}));
        throw new Error(err.detail || "Correlation failed");
      }
      const res = await resp.json();
      renderCorrelationResults(res);
    } catch (err) {
      console.error(err);
      corrResults.innerHTML = `<div class="text-danger">Failed: ${escapeHtml(err.message)}</div>`;
    }
  });

  function renderCorrelationResults(res) {
    if (!res || !res.per_rule) {
      corrResults.innerHTML = '<div class="text-muted">No results</div>';
      return;
    }

    const headers = `<tr>
      <th>Rule ID</th><th>Name</th><th>Count</th><th>Hit Rate</th><th>Avg Return</th>
    </tr>`;

    let rows = "";
    for (const [rid, info] of Object.entries(res.per_rule)) {
      const stats = info.stats || {};
      // pick lookahead = first available
      const firstH = Object.keys(stats)[0];
      const s = stats[firstH] || {count:0, hit_rate:0, avg_return:0};
      rows += `<tr>
        <td>${escapeHtml(rid)}</td>
        <td>${escapeHtml(info.name||"")}</td>
        <td>${s.count||0}</td>
        <td>${(s.hit_rate||0).toFixed(2)}</td>
        <td>${((s.avg_return||0)*100).toFixed(2)}%</td>
      </tr>`;
    }

    corrResults.innerHTML = `
      <div class="table-responsive">
        <table class="table table-sm table-dark table-striped">
          <thead class="table-dark">${headers}</thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  }

  // ---------------------- Helpers ----------------------
  function escapeHtml(str) {
    if (!str && str !== 0) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

})();
