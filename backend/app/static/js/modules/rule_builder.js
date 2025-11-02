// static/js/modules/rule_builder.js
// Vanilla nested group builder for rule_editor
// Maintains deterministic "order" fields for both groups and conditions.

export function createBuilder(rootEl, { REF, initialGroups = null } = {}) {
  if (!rootEl) throw new Error("root element required");

  const tplCond = document.getElementById("tpl-condition-row");
  const tplGroup = document.getElementById("tpl-group-card");

  function cloneTemplate(tpl) {
    return tpl.content.firstElementChild.cloneNode(true);
  }

  // create a condition row DOM, wired with change handlers
  function createConditionRow(condData = {}) {
    const node = cloneTemplate(tplCond);
    const planetSel = node.querySelector(".planet-select");
    const relationSel = node.querySelector(".relation-select");
    const targetSel = node.querySelector(".target-select");
    const orbInput = node.querySelector(".orb-input");
    const valInput = node.querySelector(".value-input");
    const removeBtn = node.querySelector(".btn-remove-cond");

    // populate planets
    planetSel.innerHTML =
      `<option value="">-- Planet --</option>` +
      (REF.planets || [])
        .map((p) => `<option value="${p.key}">${p.label}</option>`)
        .join("");

    // populate relations
    relationSel.innerHTML =
      `<option value="">-- Relation --</option>` +
      (REF.relations || [])
        .map((r) => `<option value="${r.key}">${r.label}</option>`)
        .join("");

    // handler: when relation changes, adjust target/orb/value visibility & options
    relationSel.addEventListener("change", () => {
      const relKey = relationSel.value;
      const relMeta = (REF.relations || []).find((x) => x.key === relKey);

      // reset
      targetSel.style.display = "none";
      orbInput.style.display = "none";
      valInput.style.display = "none";
      targetSel.innerHTML = "";

      if (!relMeta) return;

      // Target source
      if (relMeta.requires_target && relMeta.target_source !== "none") {
        const src =
          relMeta.target_source === "signs" ? REF.signs : REF.planets;
        targetSel.innerHTML =
          `<option value="">-- Target --</option>` +
          (src || [])
            .map((t) => `<option value="${t.key}">${t.label}</option>`)
            .join("");
        targetSel.style.display = "";
      }

      if (relMeta.has_orb) orbInput.style.display = "";
      if (relMeta.has_value) valInput.style.display = "";
    });

    // Remove action
    removeBtn.addEventListener("click", () => node.remove());

    // set initial data if provided
    if (condData) {
      if (condData.planet) planetSel.value = condData.planet;
      if (condData.relation) {
        relationSel.value = condData.relation;
        relationSel.dispatchEvent(new Event("change"));
      }
      if (condData.target) targetSel.value = condData.target;
      if (condData.orb !== undefined && condData.orb !== null)
        orbInput.value = condData.orb;
      if (condData.value !== undefined && condData.value !== null)
        valInput.value = condData.value;
    }

    return node;
  }

  // create a group card; parentGroupEl can be null for root
  function createGroupCard(parentGroupEl = null, groupData = null) {
    const groupNode = cloneTemplate(tplGroup);
    const opSel = groupNode.querySelector(".operator-select");
    const addCondBtn = groupNode.querySelector(".btn-add-cond");
    const addGroupBtn = groupNode.querySelector(".btn-add-group");
    const removeGroupBtn = groupNode.querySelector(".btn-remove-group");
    const condList = groupNode.querySelector(".conditions-list");
    const subgroupsList = groupNode.querySelector(".subgroups-list");

    // wire add cond
    addCondBtn.addEventListener("click", () => {
      const condRow = createConditionRow({});
      condList.appendChild(condRow);
    });

    // wire add subgroup
    addGroupBtn.addEventListener("click", () => {
      const subCard = createGroupCard(groupNode, null);
      subCard.style.marginLeft = "20px";
      subgroupsList.appendChild(subCard);
    });

    // remove group (if not root)
    removeGroupBtn.addEventListener("click", () => {
      if (!parentGroupEl) {
        condList.innerHTML = "";
        subgroupsList.innerHTML = "";
        opSel.value = "AND";
        return;
      }
      groupNode.remove();
    });

    // load existing groupData if provided (conditions + subgroups)
    if (groupData) {
      if (groupData.operator) opSel.value = groupData.operator;
      (groupData.conditions || []).forEach((c) => {
        const cr = createConditionRow(c);
        condList.appendChild(cr);
      });
      (groupData.subgroups || []).forEach((sg) => {
        const sc = createGroupCard(groupNode, sg);
        sc.style.marginLeft = "20px";
        subgroupsList.appendChild(sc);
      });
    }

    return groupNode;
  }

  // serialization: DOM group -> JSON group (with order tracking)
  function serializeGroup(groupNode, groupIndex = 0) {
    const opSel = groupNode.querySelector(".operator-select");
    const condListEl = groupNode.querySelector(".conditions-list");
    const condEls = Array.from(condListEl.children);
    const subgroupsEl = groupNode.querySelector(".subgroups-list");
    const subgroupEls = Array.from(subgroupsEl.children);

    const groupObj = {
      operator: opSel.value || "AND",
      order: groupIndex, // ✅ assign index-based order
      conditions: [],
      subgroups: [],
    };

    // extract conditions (with order)
    condEls.forEach((condEl, idx) => {
      const planet = condEl.querySelector(".planet-select")?.value || null;
      const relation = condEl.querySelector(".relation-select")?.value || null;
      const target = condEl.querySelector(".target-select")?.value || null;
      const orbRaw = condEl.querySelector(".orb-input")?.value;
      const valRaw = condEl.querySelector(".value-input")?.value;

      groupObj.conditions.push({
        planet: planet || null,
        relation: relation || null,
        target: target || null,
        orb: orbRaw === "" ? null : orbRaw ? parseFloat(orbRaw) : null,
        value: valRaw === "" ? null : valRaw ? parseFloat(valRaw) : null,
        order: idx, // ✅ maintain condition order
      });
    });

    // extract subgroups recursively with order
    subgroupEls.forEach((sgEl, idx) => {
      groupObj.subgroups.push(serializeGroup(sgEl, idx));
    });

    return groupObj;
  }

  // build: insert root group
  const rootGroup = createGroupCard(null, initialGroups ? initialGroups[0] : null);
  rootEl.innerHTML = "";
  rootEl.appendChild(rootGroup);

  // builder API
  return {
    rootGroupNode: rootGroup,
    getJSON: () => [serializeGroup(rootGroup)],
    setJSON: (groupsArr) => {
      rootEl.innerHTML = "";
      const g = groupsArr && groupsArr.length ? groupsArr[0] : null;
      const newRoot = createGroupCard(null, g);
      rootEl.appendChild(newRoot);
    },
    addConditionToRoot: () => {
      const cr = createConditionRow({});
      rootGroup.querySelector(".conditions-list").appendChild(cr);
    },
  };
}
