/* main.js  (ES module orchestrator)
 *
 * Integrates all Workbench modules in deterministic order.
 * Adds DOM guards so each module only runs on its own page.
 */

import { initSidebar }      from "./core/sidebar.js";
import { initI18n }         from "./core/i18n.js";
import { initAstroConfig }  from "./core/astro_config.js";

import { initEphemeris }    from "./modules/ephemeris.js";
import { initRules }        from "./modules/rules.js";
import { initSectors }      from "./modules/sectors.js";
import { initEvents }       from "./modules/events.js";
import { initRuleEditor }   from "./modules/rule_editor.js";

console.info("🪐 Astro Workbench: initializing modules…");

document.addEventListener("DOMContentLoaded", async () => {
  try {
    /* -------- Core modules -------- */
    console.time("core:init");
    initI18n();          // translations before UI render
    initSidebar();       // navigation + pane visibility
    initAstroConfig();   // location, timezone, ayanamsa
    console.timeEnd("core:init");

    /* -------- Domain modules -------- */
    console.time("domain:init");

    if (document.querySelector("#ephemerisGrid"))
      initEphemeris();

    if (document.querySelector("#rulesTable"))
      initRules();

    if (document.querySelector("#sectorsTable"))
      initSectors();

    if (document.querySelector("#eventsTable"))
      initEvents();

    if (document.querySelector("#root-group-target"))
      initRuleEditor();     // rule editor page only

    console.timeEnd("domain:init");
    console.info("✅ All modules initialized successfully");
  } catch (err) {
    console.error("❌ Workbench initialization failed:", err);
    const { toast } = await import("./core/utils.js");
    toast("Workbench initialization failed", "danger");
  }
});
