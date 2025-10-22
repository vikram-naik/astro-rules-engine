// ---------------------- RULES ----------------------

const rulesBody = document.getElementById("rulesBody");
const btnAddRule = document.getElementById("btnAddRule");

// Modals
const ruleModalEl = document.getElementById("ruleModal");
const ruleModal = new bootstrap.Modal(ruleModalEl);

// Forms
const ruleForm = document.getElementById("ruleForm");

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
        <td>${(r.confidence || 0).toFixed(2)}</td>
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