/* modules/rule_editor.js
 *
 * Refactored faithfully from your working script.
 * Uses REF.*, SECTORS, and retains dynamic dropdown logic.
 * Exports: initRuleEditor()
 */

import { toast, fetchJSON, escapeHtml, useTemplate } from "../core/utils.js";
import { loadSectors, loadReference } from "../core/ref_data.js";


// ---------- MAIN INITIALIZER ----------
export async function initRuleEditor() {
  try {
    await loadReference();
    await loadSectors();

    console.info("[rule_editor] initialized:",
      "SECTORS:", window.SECTORS?.length,
      "REF.effects:", REF?.effects?.length
    );

    const addConditionBtn = document.getElementById("btnAddCondition");
    const container = document.getElementById("conditionsContainer");
    const saveBtn = document.getElementById("btnSaveRule");

    if (!container) {
      console.warn("[rule_editor] No conditions container found, aborting init");
      return;
    }

    const ruleIdMatch = window.location.pathname.match(/rule-editor\/([^/]+)/);
    const ruleId = ruleIdMatch ? ruleIdMatch[1] : null;
    const isEditMode = !!ruleId && ruleId !== "new";
    console.log(`[rule_editor] Mode: ${isEditMode ? "Edit" : "Add"}`, ruleId || "");

    /* ---------- dropdown helpers ---------- */
    function fillDropdown(el, arr, getValue = (x) => x.key, getLabel = (x) => x.label) {
      if (!el) return;
      el.innerHTML = '<option value="">-- Select --</option>';
      (arr || []).forEach((item) => {
        const opt = document.createElement("option");
        opt.value = getValue(item);
        opt.textContent = getLabel(item);
        el.appendChild(opt);
      });
      el.value = "";
    }

    function fillDropdownPreserve(el, arr, getValue, getLabel, explicitValue = null) {
      if (!el) return;
      const prev = explicitValue !== null ? explicitValue : el.value;
      el.innerHTML = '<option value="">-- Select --</option>';
      (arr || []).forEach((item) => {
        const opt = document.createElement("option");
        opt.value = getValue(item);
        opt.textContent = getLabel(item);
        el.appendChild(opt);
      });
      if (prev) {
        const exists = Array.from(el.options).some(o => String(o.value) === String(prev));
        el.value = exists ? prev : "";
      } else el.value = "";
    }

    /* ---------- populate sector & effect ---------- */
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

    /* ---------- condition rows ---------- */
    function createConditionRow(data = {}, isFirst = false) {
      // Clone via shared helper
      const fragment = useTemplate("condition-row-template");
      const row = fragment.querySelector(".condition-row");
      if (!row) {
        console.error("[rule_editor] Template clone missing .condition-row element");
        return null;
      }

      // Remove labels for non-first rows (matches prior behavior)
      if (!isFirst) {
        row.querySelectorAll("label").forEach(lbl => (lbl.textContent = ""));
      }

      // Append to container
      container.appendChild(fragment);

      // Query controls inside this row
      const planetSel = row.querySelector(".planet-select");
      const relationSel = row.querySelector(".relation-select");
      const targetSel = row.querySelector(".target-select");
      const valueInput = row.querySelector(".value-input");
      const orbInput = row.querySelector(".orb-input");
      const removeBtn = row.querySelector(".btn-remove");

      // Populate dropdowns
      fillDropdown(planetSel, REF.planets);
      fillDropdown(relationSel, REF.relations);
      fillDropdown(targetSel, REF.planets || []);

      // Restore field values (for edit mode)
      planetSel.value = data.planet || "";
      relationSel.value = data.relation || "";
      targetSel.value = data.target || "";
      valueInput.value = data.value || "";
      orbInput.value = data.orb || "";

      // Wire events
      relationSel.addEventListener("change", (e) =>
        handleRelationChange(e.target.value, row)
      );
      removeBtn.addEventListener("click", () => row.remove());

      // Initialize relation-specific UI state
      if (data.relation) handleRelationChange(data.relation, row);

      return row;
    }

    function handleRelationChange(relationKey, row) {
      if (!row) return;
      const relationMeta = REF.relations.find(r => r.key === relationKey);
      if (!relationMeta) return;

      const planetSel = row.querySelector(".planet-select");
      const targetSel = row.querySelector(".target-select");
      const orbInput = row.querySelector(".orb-input");
      const valueInput = row.querySelector(".value-input");

      const prevPlanet = planetSel.value;
      const prevTarget = targetSel.value;
      const prevOrb = orbInput.value;
      const prevValue = valueInput.value;

      [planetSel, targetSel, orbInput, valueInput].forEach(el => (el.disabled = false));

      if (!relationMeta.requires_planet) {
        planetSel.value = "";
        planetSel.disabled = true;
      } else {
        fillDropdownPreserve(planetSel, REF.planets, (x) => x.key, (x) => x.label, prevPlanet);
      }

      if (!relationMeta.requires_target || relationMeta.target_source === "none") {
        targetSel.innerHTML = '<option value="">N/A</option>';
        targetSel.value = "";
        targetSel.disabled = true;
      } else if (relationMeta.target_source === "signs") {
        fillDropdownPreserve(targetSel, REF.signs, (x) => x.key, (x) => x.label, prevTarget);
      } else {
        fillDropdownPreserve(targetSel, REF.planets, (x) => x.key, (x) => x.label, prevTarget);
      }

      orbInput.disabled = !relationMeta.has_orb;
      valueInput.disabled = !relationMeta.has_value;
      orbInput.value = relationMeta.has_orb ? prevOrb : "";
      valueInput.value = relationMeta.has_value ? prevValue : "";
    }

    function gatherConditions() {
      return Array.from(document.querySelectorAll(".condition-row")).map((row) => ({
        planet: row.querySelector(".planet-select").value,
        relation: row.querySelector(".relation-select").value,
        target: row.querySelector(".target-select").value,
        orb: parseFloat(row.querySelector(".orb-input").value || 0),
        value: parseFloat(row.querySelector(".value-input").value || 0),
      }));
    }

    async function loadExistingRule() {
      if (!isEditMode) {
        document.getElementById("ruleEditorTitle").textContent = "Add Rule";
        createConditionRow({}, true);
        return;
      }

      document.getElementById("ruleEditorTitle").textContent = "Edit Rule";
      try {
        const r = await fetchJSON(`/api/rules/${ruleId}`);
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
        toast("Failed to load rule", "danger");
      }
    }

    if (addConditionBtn)
      addConditionBtn.addEventListener("click", () => {
        const isFirst = container.querySelectorAll(".condition-row").length === 0;
        createConditionRow({}, isFirst);
      });

    if (saveBtn)
      saveBtn.addEventListener("click", async () => {
        const name = document.getElementById("rule_name").value.trim();
        if (!name) return toast("Rule name required", "warning");

        const payload = {
          name,
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
          const res = await fetch(
            isEditMode ? `/api/rules/${ruleId}` : `/api/rules/`,
            {
              method: isEditMode ? "PUT" : "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            }
          );
          if (!res.ok) throw new Error(await res.text());
          toast(`Rule ${isEditMode ? "updated" : "created"} successfully!`, "success");
          window.location.href = "/ui/workbench";
        } catch (err) {
          console.error(err);
          toast("Failed to save rule: " + err.message, "danger");
        }
      });

    await loadExistingRule();
  } catch (err) {
    console.error("[rule_editor] init failed:", err);
    toast("Rule editor initialization failed", "danger");
  }
}
