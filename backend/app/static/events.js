(() => {
  // ============================================================
  // EVENTS MODULE
  // Handles rule-based event listing and generation
  // ============================================================

  const ruleSelect = document.getElementById("eventRuleSelect");
  const startDateInput = document.getElementById("eventStart");
  const endDateInput = document.getElementById("eventEnd");
  const providerSelect = document.getElementById("eventProvider");
  const overwriteCheckbox = document.getElementById("eventOverwrite");
  const generateBtn = document.getElementById("btnGenerateEvents");
  const resultContainer = document.getElementById("eventResults");

  //----------------------------------------------------------------
  // Load all rules into dropdown
  //----------------------------------------------------------------
  async function loadRulesForEvents() {
    resultContainer.innerHTML = `<div class="text-muted">Loading rules...</div>`;
    try {
      const resp = await fetch("/api/rules");
      if (!resp.ok) throw new Error("Failed to fetch rules");
      const rules = await resp.json();
      if (!rules.length) {
        ruleSelect.innerHTML = `<option value="">No rules found</option>`;
        resultContainer.innerHTML = `<div class="text-muted">No rules available.</div>`;
        return;
      }
      ruleSelect.innerHTML = rules
        .map((r) => `<option value="${r.rule_id}">${escapeHtml(r.name)}</option>`)
        .join("");
      resultContainer.innerHTML = `<div class="text-muted">Select a rule to view events.</div>`;
    } catch (err) {
      console.error("Error loading rules:", err);
      resultContainer.innerHTML = `<div class="text-danger">Error loading rules.</div>`;
    }
  }

  //----------------------------------------------------------------
  // Fetch events for selected rule
  //----------------------------------------------------------------
  async function fetchEventsForRule(ruleId) {
    if (!ruleId) {
      resultContainer.innerHTML = `<div class="text-muted">Select a rule to view events.</div>`;
      return;
    }

    resultContainer.innerHTML = `<div class="text-muted">Loading events...</div>`;
    try {
      const resp = await fetch(`/api/rules/${ruleId}/events`);
      if (!resp.ok) throw new Error("Failed to fetch events");
      const events = await resp.json();

      if (!events.length) {
        resultContainer.innerHTML = `<div class="text-muted">No events found for this rule.</div>`;
        return;
      }

      renderEventsTable(events);
    } catch (err) {
      console.error("Error loading events:", err);
      resultContainer.innerHTML = `<div class="text-danger">Error loading events.</div>`;
    }
  }

  //----------------------------------------------------------------
  // Generate new events for selected rule
  //----------------------------------------------------------------
  async function generateEvents() {
    const ruleId = ruleSelect.value;
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;
    const provider = providerSelect.value || "swisseph";
    const overwrite = overwriteCheckbox.checked;

    if (!ruleId) {
      alert("Please select a rule first.");
      return;
    }
    if (!startDate || !endDate) {
      alert("Please select a valid start and end date.");
      return;
    }

    resultContainer.innerHTML = `<div class="text-muted">Generating events...</div>`;

    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      provider: provider,
      overwrite: overwrite.toString(),
    });

    try {
      const resp = await fetch(`/api/rules/${ruleId}/generate_events?${params.toString()}`, {
        method: "POST",
      });
      if (!resp.ok) {
        const errText = await resp.text();
        throw new Error(errText || "Failed to generate events");
      }
      const events = await resp.json();
      renderEventsTable(events);
    } catch (err) {
      console.error("Error generating events:", err);
      resultContainer.innerHTML = `<div class="text-danger">Error generating events: ${escapeHtml(err.message)}</div>`;
    }
  }

  //----------------------------------------------------------------
  // Render events table
  //----------------------------------------------------------------
  function renderEventsTable(events) {
    if (!events || !events.length) {
      resultContainer.innerHTML = `<div class="text-muted">No events found for selected rule.</div>`;
      return;
    }

    let html = `
      <table class="table table-dark table-striped table-sm align-middle">
        <thead>
          <tr>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Provider</th>
            <th>Duration</th>
            <th>Type</th>
            <th>Subtype</th>
            <th>Metadata</th>
          </tr>
        </thead>
        <tbody>
    `;

    for (const e of events) {
      html += `
        <tr>
          <td>${escapeHtml(e.start_date || "")}</td>
          <td>${escapeHtml(e.end_date || "")}</td>
          <td>${escapeHtml(e.provider || "")}</td>
          <td>${escapeHtml(e.duration_type || "–")}</td>
          <td>${escapeHtml(e.event_type || "")}</td>
          <td>${escapeHtml(e.event_subtype || "")}</td>
          <td><pre class="mb-0 small text-muted">${escapeHtml(
            JSON.stringify(e.metadata_json, null, 1)
          )}</pre></td>
        </tr>
      `;
    }

    html += `</tbody></table>`;
    resultContainer.innerHTML = html;
  }

  //----------------------------------------------------------------
  // Event listeners
  //----------------------------------------------------------------
  ruleSelect.addEventListener("change", (e) => fetchEventsForRule(e.target.value));
  generateBtn.addEventListener("click", generateEvents);
  document.getElementById("events-tab").addEventListener("click", loadRulesForEvents);

  //----------------------------------------------------------------
  // Module export
  //----------------------------------------------------------------
  window.loadEvents = loadRulesForEvents;
})();
