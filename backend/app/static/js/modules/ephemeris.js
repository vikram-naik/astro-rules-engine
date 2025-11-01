/* modules/ephemeris.js — Vedic Ephemeris Matrix (Jyotish)
 * Drop-in revision:
 *  - extra debug logging
 *  - date column center alignment
 *  - per-column cellStyle to avoid unintended wrapping (ellipsis)
 *  - keep transition line wrap enabled (second line)
 *
 * Replace your current file with this content.
 */

import { toast, fetchJSON, showOverlay, escapeHtml } from "../core/utils.js";
import { safeT } from "../core/i18n.js";
import { onLocaleChange } from "../core/i18n.js";

let gridApi = null;
let currentStartDate = null;

/* -----------------------------
 * Load Ephemeris Data
 * ----------------------------- */
async function loadEphemeris(forceRefresh = false) {
  const startDate = currentStartDate || new Date().toISOString().split("T")[0];
  const payload = { start_date: startDate, force_refresh: !!forceRefresh };
  const overlay = document.getElementById("ephemerisLoadingOverlay");
  showOverlay(overlay, true);

  console.debug("🪐 loadEphemeris", { startDate, forceRefresh });

  try {
    const data = await fetchJSON("/api/ephemeris/matrix", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderGrid(data);
    updateMeta(data.meta);
  } catch (err) {
    console.error("❌ Ephemeris fetch failed:", err);
    toast("Failed to load ephemeris data", "danger");
    showOverlay(overlay, false);
  }
}

/* -----------------------------
 * Cell Renderer
 * ----------------------------- */
function ephemerisCellRenderer(params) {
  const v = params?.value;
  if (!v) return "";

  // parse DMS (either stringified JSON or object)
  let dms = { deg: "--", min: "--", sec: "--" };
  try {
    dms = typeof v.longitude_dms === "string"
      ? JSON.parse(v.longitude_dms)
      : v.longitude_dms || dms;
  } catch (err) {
    // fallback: keep placeholders
  }

  const d = (dms.deg ?? "--").toString().padStart(2, "0");
  const m = (dms.min ?? "--").toString().padStart(2, "0");
  const s = (dms.sec ?? "--").toString().padStart(2, "0");

  const signKey = v.sign || "";
  const signLabel = safeT(`ephemeris.signs.${signKey}`) || signKey;
  // NB: non-breaking space before sign so it doesn't wrap from degrees
  const posStr = `${d}°${m}'${s}"\u00A0${escapeHtml(signLabel)}`;

  // Flags (now each as colored <span data-flag="...">)
  const flags = [];
  // if (v.transition_from && v.transition_to) flags.push("Sg");
  if (v.dignity === "Ex") flags.push("Ex");
  if (v.dignity === "Db") flags.push("Db");
  if (v.dignity === "MT") flags.push("MT");
  if (v.combust) flags.push("C");
  if (v.is_retrograde) flags.push("R");
  if (v.is_stationary) flags.push("S");
  if (!v.is_retrograde && !v.is_stationary) flags.push("D");

const statusHtml = flags.length
  ? `<span class="ephem-status">${flags
      .map(f => {
        if (f === "Ex") return `<span data-flag="${f}" title="${safeT("ephemeris.legend.Ex") || "Exalted"}">\u2B06</span>`;
        if (f === "Db") return `<span data-flag="${f}" title="${safeT("ephemeris.legend.Db") || "Debilitated"}">\u2B07</span>`;
        if (f === "C") return `<span data-flag="${f}" title="${safeT("ephemeris.legend.C") || "Combust"}">\u2600</span>`;
        return `<span data-flag="${f}">[${f}]</span>`;
      })
      .join("")}</span>`
  : "";

  let transitionHtml = "";
  if (v.transition_from && v.transition_to && v.transition_time_local) {
    const fromLabel = safeT(`ephemeris.signs.${v.transition_from}`) || v.transition_from;
    const toLabel = safeT(`ephemeris.signs.${v.transition_to}`) || v.transition_to;
    const time = escapeHtml(v.transition_time_local);
    // note: allow wrapping on the transition line (ephem-transition class)
    transitionHtml = `<div class="ephem-transition">${safeT("ephemeris.labels.ingress")} ${escapeHtml(fromLabel)}→${escapeHtml(toLabel)} (${time})</div>`;
  }

  // structure: top line (pos + small status tags), optional second line (transition)
  // top line is non-wrapping; transition line allowed to wrap.
  return `<div class="ephem-cell">
            <div class="ephem-pos" style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
              ${posStr} ${statusHtml}
            </div>
            ${transitionHtml}
          </div>`;
}

/* -----------------------------
 * Render AG Grid
 * ----------------------------- */
function renderGrid(data) {
  if (!data || !Array.isArray(data.rows) || !Array.isArray(data.planets)) {
    toast(safeT("ephemeris.invalidData") || "Invalid ephemeris data", "warning");
    return;
  }

  const gridDiv = document.getElementById("ephemerisGrid");
  if (!gridDiv) return;

  // destroy previous grid if any
  if (gridApi && gridApi.destroy) {
    try {
      gridApi.destroy();
      gridDiv.innerHTML = "";
    } catch (e) {
      console.warn("🪐 previous grid destroy failed", e);
    }
    gridApi = null;
  }

  gridDiv.classList.add("ag-theme-alpine-dark");
  // keep grid container height controlled in CSS; fallback here
  gridDiv.style.height = gridDiv.style.height || "520px";

  const planets = data.planets;
  // Date column (center aligned)
  const colDefs = [
    {
      field: "date",
      headerName: safeT("ephemeris.columns.date") || "Date",
      valueFormatter: (p) => {
        const d = new Date(p.value);
        return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
      },
      pinned: "left",
      width: 90,
      minWidth: 70,
      cellClass: "text-light",
      cellStyle: { textAlign: "center", whiteSpace: "nowrap" },
      headerClass: "ag-center-cell",
    },
    ...planets.map((p) => ({
      field: p,
      headerName: safeT(`ephemeris.columns.${p}`) || p,
      cellRenderer: ephemerisCellRenderer,
      resizable: true,
      width: 180,
      minWidth: 160,
      maxWidth: 260,
      autoHeight: false,
      cellStyle: {
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
        minWidth: "100%",
      },
      tooltipValueGetter: (params) => {
        const v = params.value;
        if (!v) return "";
        const signKey = v.sign ? safeT(`ephemeris.signs.${v.sign}`) : "";
        const motion = v.is_retrograde
          ? safeT("ephemeris.motion.retrograde")
          : v.is_stationary
            ? safeT("ephemeris.motion.stationary")
            : safeT("ephemeris.motion.direct");
        return `${safeT(`ephemeris.columns.${params.colDef.field}`)} ${v.longitude?.toFixed(2)}° ${signKey} — ${motion}`;
      },
      cellClass: "text-light",
      // prevent planet top line wrapping; transition line is allowed by renderer
      cellStyle: { whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
    })),
  ];

  // row data mapping (planets are keys)
  const rowData = data.rows.map((r) => {
    const row = { date: r.date };
    for (const [planet, cell] of Object.entries(r.cells || {})) row[planet] = cell;
    return row;
  });

  const overlay = document.getElementById("ephemerisLoadingOverlay");

  const gridOptions = {
    columnDefs: colDefs,
    rowData,
    domLayout: "normal",
    rowHeight: 36,
    autoSizeStrategy: { type: 'fitCellContents' },
    animateRows: false,
    suppressMenuHide: true,
    suppressColumnVirtualisation: false,
    defaultColDef: {
      resizable: true,
      sortable: false,
      filter: false,
      // we want cells to appear as single-line with ellipsis by default
      cellStyle: { fontSize: "0.85rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
    },

    /* compute row height (log each decision) */
    getRowHeight: (params) => {
      const data = params.data || {};
      const planetKeys = Object.keys(data).filter((k) => k !== "date");
      const hasTransition = planetKeys.some((key) => {
        const cell = data[key];
        return cell && cell.transition_from && cell.transition_to;
      });
      // base height for single-line row; second line when a transition exists
      const h = hasTransition ? 64 : 36;
      console.debug(`🪐 RowHeight | date=${data.date || "?"} | hasTransition=${hasTransition} | height=${h}`);
      return h;
    },

    onGridReady: (params) => {
      gridApi = params.api;
      console.debug("🔧 onGridReady invoked", { rowCount: gridApi.getDisplayedRowCount() });
      // small delay to let grid render, then recompute heights and keep columns as-is (no sizeToFit)
      setTimeout(() => {
        try {
          console.debug("🔧 onGridReady → resetRowHeights()");
          gridApi.resetRowHeights();
          gridApi.redrawRows();
        } catch (e) {
          console.warn("⚠️ onGridReady resetRowHeights failed", e);
        }
      }, 120);
    },

    onFirstDataRendered: (params) => {
      showOverlay(overlay, false);
      requestAnimationFrame(() => {
        try {
          console.debug("🔧 onFirstDataRendered → resetRowHeights + redrawRows()");
          gridApi.resetRowHeights();
          gridApi.redrawRows();
        } catch (e) {
          console.warn("⚠️ firstDataRendered reset/redraw failed", e);
        }
      });

      // enforce sane column widths if some defs went tiny
      try {
        const defs = gridApi.getColumnDefs();
        defs.forEach((c) => {
          if (!c.width || c.width < 120) c.width = 150;
        });
        // updateGridOptions is recommended over setColumnDefs per ag-grid deprecation warnings
        gridApi.updateGridOptions({ columnDefs: defs });
        // don't auto fit — we want horizontal scroll when columns overflow
      } catch (e) {
        console.warn("⚠️ column width enforcement failed", e);
      }
    },

    onGridSizeChanged: () => {
      try {
        console.debug("🔧 onGridSizeChanged → resetRowHeights()");
        gridApi.resetRowHeights();
      } catch (e) {
        console.warn("⚠️ gridSizeChanged handler failed", e);
      }
    },
  };

  try {
    const gridInstance = agGrid.createGrid(gridDiv, gridOptions);
    gridApi = gridInstance.api;
    // small debug: print columns summary
    setTimeout(() => {
      try {
        const cols = gridApi.getAllGridColumns().map(c => ({ id: c.getId(), width: c.getActualWidth() }));
        console.debug("🪐 Column widths after init:", cols);
      } catch (e) { /* ignore in older ag-grid where API differs */ }
    }, 300);
  } catch (err) {
    console.error("⚠️ AG Grid init failed:", err);
    toast("Failed to initialize grid", "danger");
  }
}

/* -----------------------------
 * Update footer legend
 * ----------------------------- */
function updateMeta(meta) {
  const footer = document.querySelector(".card-footer");
  if (!footer) return;
  footer.innerHTML = `
  <div class="text-secondary small ephem-legend">
    <span class="ephem-status">
      <span data-flag="Ex">\u2B06</span> ${safeT("ephemeris.legend.Ex")} · 
      <span data-flag="Db">\u2B07</span> ${safeT("ephemeris.legend.Db")} · 
      <span data-flag="MT">[MT]</span> ${safeT("ephemeris.legend.MT")} · 
      <span data-flag="C">\u2600</span> ${safeT("ephemeris.legend.C")} · 
      <span data-flag="R">[R]</span> ${safeT("ephemeris.legend.R")} · 
      <span data-flag="D">[D]</span> ${safeT("ephemeris.legend.D")} · 
      <span data-flag="S">[S]</span> ${safeT("ephemeris.legend.S")}
    </span>
  </div>`;
}

/* -----------------------------
 * Navigation
 * ----------------------------- */
function shiftWeek(days) {
  const d = new Date(currentStartDate);
  d.setDate(d.getDate() + days);
  currentStartDate = d.toISOString().split("T")[0];
  document.getElementById("ephemerisStartDate").value = currentStartDate;
  loadEphemeris(false);
}

/* -----------------------------
 * Init
 * ----------------------------- */
export function initEphemeris() {
  const startDateInput = document.getElementById("ephemerisStartDate");
  const btnPrev = document.getElementById("ephemerisPrev");
  const btnNext = document.getElementById("ephemerisNext");
  const btnRefresh = document.getElementById("ephemerisRefresh");

  if (!startDateInput) return;

  const today = new Date().toISOString().split("T")[0];
  startDateInput.value = today;
  currentStartDate = today;

  btnPrev?.addEventListener("click", () => shiftWeek(-7));
  btnNext?.addEventListener("click", () => shiftWeek(7));
  btnRefresh?.addEventListener("click", () => loadEphemeris(true));
  startDateInput.addEventListener("change", (e) => {
    currentStartDate = e.target.value;
    loadEphemeris(true);
  });

  loadEphemeris(false);



  onLocaleChange(() => {
    try {
      if (!gridApi) return;
      console.debug("🌐 Locale changed – refreshing grid headers");

      // Update header names and tooltips for current columns
      const updatedCols = gridApi.getColumnDefs().map(col => {
        if (col.field === "date") {
          col.headerName = safeT("ephemeris.columns.date") || "Date";
        } else {
          col.headerName = safeT(`ephemeris.columns.${col.field}`) || col.field;
        }
        return col;
      });

      // Apply new localized column definitions
      gridApi.setGridOption("columnDefs", updatedCols);

      // Redraw all visible cells to refresh text rendered via safeT()
      gridApi.refreshCells({ force: true });
      gridApi.refreshHeader();
      gridApi.redrawRows();
      updateMeta({}); // re-renders footer legend with new safeT()

      toast(safeT("ephemeris.labels.localeUpdated") || "Grid refreshed for new language", "info");
    } catch (err) {
      console.warn("🌐 Locale change refresh failed:", err);
    }
  });


}
