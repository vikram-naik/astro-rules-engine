// =============================
// rule_editor.js (Final Refined Version)
// =============================

document.addEventListener("DOMContentLoaded", async () => {
  await loadReference();
  await loadSectors();

  console.debug("[rule_editor] loadSectors done",
    "SECTORS:", window.SECTORS ? window.SECTORS.length : "undefined",
    "REF.effects:", REF && REF.effects ? REF.effects.length : "undefined"
  );

  const addConditionBtn = document.getElementById("btnAddCondition");
  const container = document.getElementById("conditionsContainer");
  const saveBtn = document.getElementById("btnSaveRule");

  const ruleIdMatch = window.location.pathname.match(/rule-editor\/(\w+)/);
  const isEditMode = !!ruleIdMatch;
  const ruleId = isEditMode ? ruleIdMatch[1] : null;

  // ----------------------------------------------
  // Dropdown helpers
  // ----------------------------------------------
  function fillDropdown(el, arr, getValue = (x) => x.key, getLabel = (x) => x.label) {
    if (!el) return;
    el.innerHTML = '<option value="">-- Select --</option>';
    (arr || []).forEach((item) => {
      const opt = document.createElement("option");
      opt.value = getValue(item);
      opt.textContent = getLabel(item);
      el.appendChild(opt);
    });
    el.value = ""; // ensure placeholder selected
  }

  // Helper: populate a select but preserve current value if still available.
  function fillDropdownPreserve(el, arr, getValue = (x) => x.key, getLabel = (x) => x.label, explicitValue = null) {
    if (!el) return;
    const prev = explicitValue !== null ? explicitValue : el.value;

    el.innerHTML = '<option value="">-- Select --</option>';
    (arr || []).forEach(item => {
      const opt = document.createElement("option");
      opt.value = getValue(item);
      opt.textContent = getLabel(item);
      el.appendChild(opt);
    });

    // Re-select previous value if still valid
    if (prev) {
      const exists = Array.from(el.options).some(o => String(o.value) === String(prev));
      if (exists) {
        el.value = prev;
      } else {
        el.value = "";
      }
    } else {
      el.value = "";
    }
  }

  // ----------------------------------------------
  // Populate sector & effect dropdowns
  // ----------------------------------------------
  const sectorSel = document.getElementById("rule_sector");
  const effectSel = document.getElementById("rule_effect");

  if (sectorSel && window.SECTORS?.length) {
    sectorSel.innerHTML = '<option value="">-- Select Sector --</option>' +
      window.SECTORS.map(s =>
        `<option value="${s.id}">${escapeHtml(s.name)} (${escapeHtml(s.code)})</option>`
      ).join("");
  }

  if (effectSel && REF.effects?.length) {
    effectSel.innerHTML = '<option value="">-- Select Effect --</option>' +
      REF.effects.map(e => `<option value="${e.key}">${escapeHtml(e.label)}</option>`).join("");
  }

  // ----------------------------------------------
  // Condition Row Creation
  // ----------------------------------------------
  function createConditionRow(data = {}, isFirst = false) {
    console.log("createConditionRow", data, isFirst) 
    const row = document.createElement("div");
    row.className = "row g-2 align-items-end mb-2 condition-row";

    const labelHtml = (text) => (isFirst ? `<label class="form-label small">${text}</label>` : "");

    row.innerHTML = `
      <div class="col-md-2">
        ${labelHtml("Planet")}
        <select class="form-select form-select-sm planet-select"></select>
      </div>
      <div class="col-md-3">
        ${labelHtml("Relation")}
        <select class="form-select form-select-sm relation-select"></select>
      </div>
      <div class="col-md-3">
        ${labelHtml("Target")}
        <select class="form-select form-select-sm target-select"></select>
      </div>
      <div class="col-md-2">
        ${labelHtml("Value")}
        <input type="number" step="0.1" placeholder="Value"
               class="form-control form-control-sm value-input">
      </div>
      <div class="col-md-1">
        ${labelHtml("Orb")}
        <input type="number" step="0.1" placeholder="Orb"
               class="form-control form-control-sm orb-input">
      </div>
      <div class="col-md-1 text-center">
        ${isFirst ? "<label class='form-label small'>&nbsp;</label>" : ""}
        <button class="btn btn-sm btn-outline-danger btn-remove">×</button>
      </div>
    `;

    container.appendChild(row);

    const planetSel = row.querySelector(".planet-select");
    const relationSel = row.querySelector(".relation-select");
    const targetSel = row.querySelector(".target-select");

    fillDropdown(planetSel, REF.planets);
    fillDropdown(relationSel, REF.relations);

    // Determine target dropdown source based on relation (for edit mode)
    if (data.relation) {
      const relationMeta = REF.relations.find(r => r.key === data.relation);
      if (relationMeta) {
        if (relationMeta.target_source === "signs") {
          fillDropdown(targetSel, REF.signs || []);
        } else if (relationMeta.target_source === "planets") {
          fillDropdown(targetSel, REF.planets || []);
        } else {
          // e.g., none
          targetSel.innerHTML = '<option value="">N/A</option>';
          targetSel.disabled = true;
        }
      } else {
        fillDropdown(targetSel, REF.planets || []);
      }
    } else {
      // new (add mode)
      fillDropdown(targetSel, REF.planets || []);
    }


    planetSel.value = data.planet || "";
    relationSel.value = data.relation || "";
    targetSel.value = data.target || "";
    row.querySelector(".value-input").value = data.value || "";
    row.querySelector(".orb-input").value = data.orb || "";

    // Ensure default placeholders when no data provided
    if (!data.planet) planetSel.value = "";
    if (!data.relation) relationSel.value = "";
    if (!data.target) targetSel.value = "";

    // Relation-driven logic
    relationSel.addEventListener("change", (e) => {
      const rel = e.target.value;
      handleRelationChange(rel, row);
    });

    row.querySelector(".btn-remove").addEventListener("click", () => row.remove());

    if (data.relation) handleRelationChange(data.relation, row);
    return row;
  }

  // ----------------------------------------------
  // Relation-based Dynamic Behavior
  // ----------------------------------------------
  function handleRelationChange(relationKey, row) {
    console.log("handleRelationChange", relationKey, row)
    const relationMeta = REF.relations.find(r => r.key === relationKey);
    const planetSel = row.querySelector(".planet-select");
    const targetSel = row.querySelector(".target-select");
    const orbInput = row.querySelector(".orb-input");
    const valueInput = row.querySelector(".value-input");

    if (!relationMeta) {
      console.warn("No relation metadata found for", relationKey);
      return;
    }

    const prevPlanet = planetSel.value;
    const prevTarget = targetSel.value;
    const prevOrb = orbInput.value;
    const prevValue = valueInput.value;

    [planetSel, targetSel, orbInput, valueInput].forEach(el => (el.disabled = false));

    // Planet handling
    if (!relationMeta.requires_planet) {
      planetSel.value = "";
      planetSel.disabled = true;
    } else {
      fillDropdownPreserve(planetSel, REF.planets || [], (x) => x.key, (x) => x.label, prevPlanet);
    }

    // Target handling
    if (!relationMeta.requires_target || relationMeta.target_source === "none") {
      targetSel.innerHTML = '<option value="">N/A</option>';
      targetSel.value = "";
      targetSel.disabled = true;
    } else if (relationMeta.target_source === "signs") {
      console.log(targetSel, REF.signs, prevTarget )
      fillDropdownPreserve(targetSel, REF.signs || [], (x) => x.key, (x) => x.label, prevTarget);
      // explicit reapply for edit mode
      if (prevTarget && Array.from(targetSel.options).some(o => o.value === prevTarget)) {
        targetSel.value = prevTarget;
      }
    } else {
      fillDropdownPreserve(targetSel, REF.planets || [], (x) => x.key, (x) => x.label, prevTarget);
      if (prevTarget && Array.from(targetSel.options).some(o => o.value === prevTarget)) {
        targetSel.value = prevTarget;
      }
    }

    // Orb + Value
    if (!relationMeta.has_orb) {
      orbInput.value = "";
      orbInput.disabled = true;
    } else if (prevOrb) {
      orbInput.value = prevOrb;
    }

    if (!relationMeta.has_value) {
      valueInput.value = "";
      valueInput.disabled = true;
    } else if (prevValue) {
      valueInput.value = prevValue;
    }
  }

  // ----------------------------------------------
  // Gather Conditions JSON
  // ----------------------------------------------
  function gatherConditions() {
    const rows = document.querySelectorAll(".condition-row");
    return Array.from(rows).map((row) => ({
      planet: row.querySelector(".planet-select").value,
      relation: row.querySelector(".relation-select").value,
      target: row.querySelector(".target-select").value,
      orb: parseFloat(row.querySelector(".orb-input").value || 0),
      value: parseFloat(row.querySelector(".value-input").value || 0)
    }));
  }

  // ----------------------------------------------
  // Edit Mode Loader
  // ----------------------------------------------
  async function loadExistingRule() {
    if (!isEditMode) return;
    document.getElementById("ruleEditorTitle").textContent = "Edit Rule";

    try {
      const resp = await fetch(`/api/rules/${ruleId}`);
      if (!resp.ok) throw new Error("Failed to load rule");
      const r = await resp.json();

      document.getElementById("rule_name").value = r.name;
      document.getElementById("rule_confidence").value = r.confidence || 0.8;
      document.getElementById("rule_enabled").checked = r.enabled;
      document.getElementById("rule_description").value = r.description || "";

      container.innerHTML = "";
      (r.conditions || []).forEach((cond, idx) => {
        const row = createConditionRow(cond, idx === 0);
        if (cond.relation) handleRelationChange(cond.relation, row);
      });

      const out = r.outcomes?.[0] || {};
      document.getElementById("rule_sector").value = out.sector_id || "";
      document.getElementById("rule_effect").value = out.effect || "";
      document.getElementById("rule_weight").value = out.weight || 1.0;
    } catch (err) {
      console.error(err);
      alert("Failed to load rule for editing.");
    }
  }

  // ----------------------------------------------
  // Save Handler
  // ----------------------------------------------
  saveBtn.addEventListener("click", async () => {
    const ruleName = document.getElementById("rule_name").value.trim();
    if (!ruleName) return alert("Rule name required");

    const payload = {
      name: ruleName,
      confidence: parseFloat(document.getElementById("rule_confidence").value || 0.8),
      enabled: document.getElementById("rule_enabled").checked,
      description: document.getElementById("rule_description").value.trim(),
      conditions: gatherConditions(),
      outcomes: [
        {
          sector_id: document.getElementById("rule_sector").value,
          effect: document.getElementById("rule_effect").value,
          weight: parseFloat(document.getElementById("rule_weight").value || 1.0),
        },
      ],
    };

    try {
      const resp = await fetch(
        isEditMode ? `/api/rules/${ruleId}` : `/api/rules/`,
        {
          method: isEditMode ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );

      if (!resp.ok) throw new Error(await resp.text());
      alert(`✅ Rule ${isEditMode ? "updated" : "created"} successfully!`);
      window.location.href = "/ui/workbench";
    } catch (err) {
      console.error(err);
      alert(`❌ Failed to save rule: ${err.message}`);
    }
  });

  // ----------------------------------------------
  // Add Condition button
  // ----------------------------------------------
  addConditionBtn.addEventListener("click", () => {
    const isFirst = container.querySelectorAll(".condition-row").length === 0;
    createConditionRow({}, isFirst);
  });

  // ----------------------------------------------
  // Bootstrap
  // ----------------------------------------------
  createConditionRow({}, true);
  await loadExistingRule();
});
