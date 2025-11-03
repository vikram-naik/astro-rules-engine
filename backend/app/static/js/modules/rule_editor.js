/* modules/rule_editor.js
 * Vanilla Bootstrap-5 nested rule builder (no jQuery)
 */

import { toast, fetchJSON, escapeHtml } from "../core/utils.js";
import { loadSectors, loadReference } from "../core/ref_data.js";
import { t, translateNewContent } from "../core/i18n.js";
import { createBuilder } from "./rule_builder.js";

export async function initRuleEditor() {
  try {
    await loadReference();
    await loadSectors();

    const ruleIdMatch = window.location.pathname.match(/rule-editor\/([^/]+)/);
    const ruleId = ruleIdMatch ? ruleIdMatch[1] : null;
    const isEditMode = !!ruleId && ruleId !== "new";

    const saveBtn = document.getElementById("btnSaveRule");
    const sectorSel = document.getElementById("rule_sector");
    const effectSel = document.getElementById("rule_effect");

    // populate dropdowns
    if (sectorSel && window.SECTORS?.length) {
      sectorSel.innerHTML =
        '<option value="">-- Select Sector --</option>' +
        window.SECTORS
          .map(
            (s) =>
              `<option value="${s.id}">${escapeHtml(s.name)} (${escapeHtml(
                s.code
              )})</option>`
          )
          .join("");
    }

    if (effectSel && REF.effects?.length) {
      effectSel.innerHTML =
        `<option value="">${t("ruleEditor.outcome.selectEffect") || "-- Select Effect --"}</option>` +
        REF.effects
          .map((e) => {
            const lbl = t(e.i18n) || e.label;
            return `<option value="${e.key}" data-i18n="${e.i18n}">${escapeHtml(lbl)}</option>`;
          })
          .join("");
    }

    // Load existing rule if editing
    let ruleData = null;
    if (isEditMode) {
      ruleData = await fetchJSON(`/api/rules/${ruleId}`);
      document.getElementById("rule_name").value = ruleData.name;
      document.getElementById("rule_confidence").value =
        ruleData.confidence || 0.8;
      document.getElementById("rule_enabled").checked = ruleData.enabled;
      document.getElementById("rule_description").value =
        ruleData.description || "";
      const out = ruleData.outcomes?.[0] || {};
      document.getElementById("rule_sector").value = out.sector_id || "";
      document.getElementById("rule_effect").value = out.effect || "";
      document.getElementById("rule_weight").value = out.weight || 1.0;
    }

    // Create builder
    const rootEl = document.getElementById("root-group-target");
    const builder = createBuilder(rootEl, {
      REF,
      initialGroups: ruleData ? ruleData.condition_groups : null,
    });
    translateNewContent(rootEl);

    // Save handler
    saveBtn?.addEventListener("click", async () => {
      const name = document.getElementById("rule_name").value.trim();
      if (!name) return toast("Rule name required", "warning");

      const condition_groups = builder.getJSON();
      console.log("condition_groups", condition_groups)
      const payload = {
        name,
        confidence: parseFloat(
          document.getElementById("rule_confidence").value || 0.8
        ),
        enabled: document.getElementById("rule_enabled").checked,
        description: document.getElementById("rule_description").value.trim(),
        condition_groups,
        outcomes: [
          {
            sector_id: document.getElementById("rule_sector").value,
            effect: document.getElementById("rule_effect").value,
            weight: parseFloat(
              document.getElementById("rule_weight").value || 1.0
            ),
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
        toast(
          `Rule ${isEditMode ? "updated" : "created"} successfully!`,
          "success"
        );
        window.location.href = "/ui/workbench";
      } catch (err) {
        console.error(err);
        toast("Failed to save rule: " + err.message, "danger");
      }
    });
  } catch (err) {
    console.error("[rule_editor] init failed:", err);
    toast("Rule editor initialization failed", "danger");
  }
}
