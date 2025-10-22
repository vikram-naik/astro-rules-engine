// Correlation
const btnRunCorr = document.getElementById("btnRunCorr");
const corrResults = document.getElementById("corrResults");

btnRunCorr.addEventListener("click", async (e) => {
  e.preventDefault();
  corrResults.innerHTML = '<div class="text-muted">Running…</div>';

  const start = document.getElementById("corrStart").value;
  const end = document.getElementById("corrEnd").value;
  const ticker = document.getElementById("corrTicker").value || "^GSPC";
  const look = (document.getElementById("corrLookahead").value || "1,3,5").split(",").map(s => parseInt(s.trim())).filter(Boolean);

  const payload = {
    start_date: start,
    end_date: end,
    ticker: ticker,
    lookahead_days: look
  };

  try {
    const resp = await fetch("/correlation/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: "error" }));
      throw new Error(err.detail || "Correlation failed");
    }
    const res = await resp.json();
    renderCorrelationResults(res);
  } catch (err) {
    console.error(err);
    corrResults.innerHTML = `<div class="text-danger">Failed: ${escapeHtml(err.message)}</div>`;
  }
});

function renderCorrelationResults(res) {
  if (!res || !res.per_rule) {
    corrResults.innerHTML = '<div class="text-muted">No results</div>';
    return;
  }

  const headers = `<tr>
      <th>Rule ID</th><th>Name</th><th>Count</th><th>Hit Rate</th><th>Avg Return</th>
    </tr>`;

  let rows = "";
  for (const [rid, info] of Object.entries(res.per_rule)) {
    const stats = info.stats || {};
    // pick lookahead = first available
    const firstH = Object.keys(stats)[0];
    const s = stats[firstH] || { count: 0, hit_rate: 0, avg_return: 0 };
    rows += `<tr>
        <td>${escapeHtml(rid)}</td>
        <td>${escapeHtml(info.name || "")}</td>
        <td>${s.count || 0}</td>
        <td>${(s.hit_rate || 0).toFixed(2)}</td>
        <td>${((s.avg_return || 0) * 100).toFixed(2)}%</td>
      </tr>`;
  }

  corrResults.innerHTML = `
      <div class="table-responsive">
        <table class="table table-sm table-dark table-striped">
          <thead class="table-dark">${headers}</thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
}