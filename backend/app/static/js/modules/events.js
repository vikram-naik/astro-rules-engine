/* modules/events.js
 *
 * Handles Events generation based on selected rule(s)
 *
 * Exports:
 *   initEvents() – sets up event handlers and loads rules list
 */

import { toast, fetchJSON, withSpinner, escapeHtml } from "../core/utils.js";

async function loadRulesForEvents() {
  const ruleSelect = document.getElementById("eventRuleSelect");
  if (!ruleSelect) return;

  try {
    ruleSelect.innerHTML = `<option disabled selected>Loading...</option>`;
    const rules = await fetchJSON("/api/rules");

    if (!Array.isArray(rules) || rules.length === 0) {
      ruleSelect.innerHTML = `<option disabled>No rules found</option>`;
      return;
    }

    ruleSelect.innerHTML = rules
      .map(
        (r) =>
          `<option value="${escapeHtml(r.id)}">${escapeHtml(r.name)}</option>`
      )
      .join("");

  } catch (err) {
    console.error("Failed to load rules:", err);
    toast("Failed to load rules list", "danger");
    ruleSelect.innerHTML = `<option disabled>Error loading rules</option>`;
  }
}

async function generateEvents() {
  const ruleSelect = document.getElementById("eventRuleSelect");
  const startEl = document.getElementById("eventStart");
  const endEl = document.getElementById("eventEnd");
  const providerEl = document.getElementById("eventProvider");
  const tableBody = document.getElementById("eventsTableBody");
  const btn = document.getElementById("generateEventsBtn");

  if (!ruleSelect || !startEl || !endEl || !tableBody || !providerEl) {
    toast("Missing event form elements", "danger");
    return;
  }

  const ruleId = ruleSelect.value;
  const start = startEl.value;
  const end = endEl.value;
  const provider = providerEl.value;

  if (!ruleId || !start || !end) {
    toast("Please select rule and date range", "warning");
    return;
  }

  const payload = { rule_id: ruleId, start, end, provider };

  await withSpinner(btn, async () => {
    try {
      const res = await fetch("/api/events/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Generation failed");
      const events = await res.json();
      renderEvents(events);
      toast(`Generated ${events.length} events`, "success");
    } catch (err) {
      console.error("Error generating events:", err);
      toast("Failed to generate events", "danger");
    }
  });
}

function renderEvents(events = []) {
  const tableBody = document.getElementById("eventsTableBody");
  if (!tableBody) return;

  if (!Array.isArray(events) || events.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-secondary small">No events found</td></tr>`;
    return;
  }

  tableBody.innerHTML = events
    .map(
      (e) => `
    <tr>
      <td>${escapeHtml(e.rule_name || "")}</td>
      <td>${escapeHtml(e.start || "")}</td>
      <td>${escapeHtml(e.end || "")}</td>
      <td>${escapeHtml(e.provider || "")}</td>
      <td>${escapeHtml(e.description || "")}</td>
    </tr>`
    )
    .join("");
}

export function initEvents() {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initEvents);
    return;
  }

  const btn = document.getElementById("generateEventsBtn");
  const ruleSelect = document.getElementById("eventRuleSelect");

  if (btn) btn.addEventListener("click", generateEvents);
  if (ruleSelect) loadRulesForEvents();

  // Optional auto-refresh when tab is shown
  const eventsTab = document.querySelector("[data-target='#events']");
  if (eventsTab) {
    eventsTab.addEventListener("click", () => {
      loadRulesForEvents();
    });
  }
}
