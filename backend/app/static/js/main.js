/* main.js  (ES module orchestrator)
 * 
 * Integrates all Workbench modules in deterministic order.
 * Removes legacy global glue.
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
    initI18n();          // must be first so translations exist before UI render
    initSidebar();       // UI navigation + pane visibility
    initAstroConfig();   // location, timezone, ayanamsa
    console.timeEnd("core:init");

    /* -------- Domain modules -------- */
    console.time("domain:init");
    initEphemeris();
    initRules();
    initSectors();
    initEvents();
    initRuleEditor();    // only active on /rule-editor page
    console.timeEnd("domain:init");

    console.info("✅ All modules initialized successfully");
  } catch (err) {
    console.error("❌ Workbench initialization failed:", err);
    import("./core/utils.js").then(({ toast }) =>
      toast("Workbench initialization failed", "danger")
    );
  }
});
