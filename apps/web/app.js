const state = {
  apiBase: "http://127.0.0.1:8000",
  benchmarkId: null,
  mode: "strict",
  topN: 10,
  requestId: 0,
  shortlist: [],
  health: null,
  dashboard: null,
  comparison: null,
  exportRows: null,
  selectedGene: null,
};

const elements = {
  apiBaseInput: document.getElementById("apiBaseInput"),
  benchmarkSelect: document.getElementById("benchmarkSelect"),
  modeSelect: document.getElementById("modeSelect"),
  topNInput: document.getElementById("topNInput"),
  refreshButton: document.getElementById("refreshButton"),
  healthMeta: document.getElementById("healthMeta"),
  healthCard: document.getElementById("healthCard"),
  heroTitle: document.getElementById("heroTitle"),
  heroSubtitle: document.getElementById("heroSubtitle"),
  strictLeaderChip: document.getElementById("strictLeaderChip"),
  exploratoryLeaderChip: document.getElementById("exploratoryLeaderChip"),
  movementChip: document.getElementById("movementChip"),
  shortlistTableBody: document.getElementById("shortlistTableBody"),
  targetExplanationTitle: document.getElementById("targetExplanationTitle"),
  targetExplanationBody: document.getElementById("targetExplanationBody"),
  modeComparisonBody: document.getElementById("modeComparisonBody"),
  exportPreview: document.getElementById("exportPreview"),
};

function buildUrl(path, query = {}) {
  const url = new URL(path, state.apiBase);
  Object.entries(query).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
}

async function fetchJson(path, query) {
  const response = await fetch(buildUrl(path, query));
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || `Request failed for ${path}`);
  }
  return response.json();
}

async function fetchSnapshotJson(materializedPath, livePath, query, materializedQuery = query) {
  try {
    return await fetchJson(materializedPath, materializedQuery);
  } catch (error) {
    return fetchJson(livePath, query);
  }
}

function benchmarkHealthItem() {
  return state.health?.items?.find((item) => item.benchmark_id === state.benchmarkId) || null;
}

function benchmarkDashboardItem() {
  return state.dashboard?.items?.find((item) => item.benchmark_id === state.benchmarkId) || null;
}

function snapshotTopN() {
  return state.dashboard?.top_n || state.health?.top_n || state.exportRows?.top_n || null;
}

function canUseMaterializedDetails() {
  return snapshotTopN() === state.topN;
}

function setHealthStatus(message) {
  elements.healthCard.innerHTML = `<div class="metric-row"><span class="muted">${message}</span></div>`;
}

function setShortlistStatus(message) {
  elements.shortlistTableBody.innerHTML = `<tr><td colspan="5" class="muted">${message}</td></tr>`;
}

function setModeComparisonStatus(message) {
  elements.modeComparisonBody.innerHTML = `<div class="comparison-card"><span class="muted">${message}</span></div>`;
}

function setExportStatus(message) {
  elements.exportPreview.textContent = message;
}

function setExplanationStatus(message) {
  elements.targetExplanationBody.className = "explanation-body";
  elements.targetExplanationBody.innerHTML = `<div class="status-banner">${message}</div>`;
}

function renderHealthCard() {
  const benchmark = benchmarkHealthItem();
  const snapshotTopN = state.health?.top_n;
  elements.healthMeta.textContent = snapshotTopN
    ? `Latest materialized benchmark snapshot (top ${snapshotTopN}).`
    : "Latest materialized benchmark snapshot unavailable.";

  if (!benchmark) {
    setHealthStatus("No benchmark health available.");
    return;
  }

  const rows = [
    ["Readiness", benchmark.readiness_flag],
    ["Strict top-N positives", benchmark.strict_recovered_in_top_n_count],
    ["Exploratory top-N positives", benchmark.exploratory_recovered_in_top_n_count],
    ["Recovered anywhere", benchmark.recovered_anywhere_count],
  ];
  elements.healthCard.innerHTML = rows
    .map(
      ([label, value]) =>
        `<div class="metric-row"><span class="muted">${label}</span><strong>${value}</strong></div>`,
    )
    .join("");
}

function renderHero() {
  const benchmark = benchmarkHealthItem();
  const dashboardItem = benchmarkDashboardItem();
  const positive = state.comparison?.benchmark_positive_comparison?.[0] || dashboardItem?.benchmark_positive_comparison?.[0] || null;

  elements.heroTitle.textContent = state.benchmarkId || "PrioriTx";
  elements.heroSubtitle.textContent = benchmark
    ? `Readiness: ${benchmark.readiness_flag}. Strict leader ${benchmark.strict_leader?.gene_symbol || "-"}, exploratory leader ${benchmark.exploratory_leader?.gene_symbol || "-"}.`
    : "Select a benchmark to inspect source-backed prioritization outputs.";
  elements.strictLeaderChip.textContent = benchmark?.strict_leader?.gene_symbol || "-";
  elements.exploratoryLeaderChip.textContent = benchmark?.exploratory_leader?.gene_symbol || "-";
  elements.movementChip.textContent = positive?.movement || "-";
}

function renderShortlist() {
  if (!state.shortlist.length) {
    setShortlistStatus("No shortlist data available.");
    return;
  }

  elements.shortlistTableBody.innerHTML = state.shortlist
    .map((item) => {
      const positive = item.benchmark_positive_overlay?.is_source_backed_positive;
      const rationale = item.rationale?.[0] || "No rationale available.";
      return `
        <tr data-gene="${item.gene_symbol}" class="${state.selectedGene === item.gene_symbol ? "is-selected" : ""}">
          <td>${item.rank}</td>
          <td>
            <div class="gene-cell">
              <strong>${item.gene_symbol}</strong>
              <span class="muted">${item.ensembl_gene_id || "No Ensembl ID"}</span>
            </div>
          </td>
          <td>${item.score.toFixed(4)}</td>
          <td><span class="tag ${positive ? "tag-positive" : "tag-neutral"}">${positive ? "Benchmark positive" : "Candidate"}</span></td>
          <td>${rationale}</td>
        </tr>
      `;
    })
    .join("");

  elements.shortlistTableBody.querySelectorAll("tr[data-gene]").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedGene = row.dataset.gene;
      renderShortlist();
      void loadTargetExplanation();
    });
  });
}

function renderModeComparison() {
  const items = state.comparison?.benchmark_positive_comparison || [];
  if (!items.length) {
    setModeComparisonStatus("No benchmark-positive comparison available.");
    return;
  }

  elements.modeComparisonBody.innerHTML = items
    .map(
      (item) => `
        <div class="comparison-card">
          <p class="eyebrow">${item.gene_symbol}</p>
          <strong>${item.movement}</strong>
          <p class="muted">Strict rank ${item.strict_rank ?? "-"} -> exploratory rank ${item.exploratory_rank ?? "-"}</p>
        </div>
      `,
    )
    .join("");
}

function renderExportPreview() {
  const rows = state.exportRows?.rows || [];
  const benchmarkRows = rows.filter((row) => row.benchmark_id === state.benchmarkId).slice(0, 4);
  elements.exportPreview.textContent = JSON.stringify(benchmarkRows, null, 2);
}

function renderExplanation(payload) {
  elements.targetExplanationTitle.textContent = payload.gene_symbol;
  const rationale = (payload.rationale || []).map((item) => `<li>${item}</li>`).join("");
  const caveats = (payload.caveats || []).map((item) => `<li>${item}</li>`).join("");
  elements.targetExplanationBody.className = "explanation-body";
  elements.targetExplanationBody.innerHTML = `
    <div class="explanation-card">
      <p>${payload.overview}</p>
      <strong>Rationale</strong>
      <ul class="bullet-list">${rationale || "<li>No rationale available.</li>"}</ul>
    </div>
    <div class="caveat-card">
      <strong>Caveats</strong>
      <ul class="bullet-list">${caveats || "<li>No caveats reported.</li>"}</ul>
    </div>
  `;
}

async function loadTargetExplanation() {
  if (!state.selectedGene || !state.benchmarkId) {
    return;
  }

  setExplanationStatus(`Loading ${state.selectedGene} explanation...`);
  try {
    const payload = await fetchJson("/target-explanation", {
      benchmark_id: state.benchmarkId,
      gene_symbol: state.selectedGene,
      mode: state.mode,
      top_n: state.topN,
    });
    if (payload.gene_symbol !== state.selectedGene) {
      return;
    }
    renderExplanation(payload);
  } catch (error) {
    setExplanationStatus(error.message);
  }
}

async function loadSnapshotSummary(requestId) {
  setHealthStatus("Loading benchmark health snapshot...");
  setExportStatus("Loading export snapshot...");

  try {
    const [dashboard, health, exportRows] = await Promise.all([
      fetchSnapshotJson("/materialized/benchmark-dashboard-summary", "/benchmark-dashboard-summary", { top_n: state.topN }),
      fetchSnapshotJson("/materialized/benchmark-health-summary", "/benchmark-health-summary", { top_n: state.topN }),
      fetchSnapshotJson("/materialized/benchmark-health-export", "/benchmark-health-export", { top_n: state.topN }),
    ]);

    if (requestId !== state.requestId) {
      return;
    }

    state.dashboard = dashboard;
    state.health = health;
    state.exportRows = exportRows;
    renderHealthCard();
    renderHero();
    renderExportPreview();
  } catch (error) {
    if (requestId !== state.requestId) {
      return;
    }
    elements.healthMeta.textContent = "Unable to load benchmark snapshot.";
    setHealthStatus(error.message);
    setExportStatus(error.message);
  }
}

async function loadModeComparison(requestId) {
  setModeComparisonStatus("Loading strict vs exploratory comparison...");
  try {
    const comparison = canUseMaterializedDetails()
      ? await fetchSnapshotJson(
          "/materialized/benchmark-mode-comparison",
          "/benchmark-mode-comparison",
          { benchmark_id: state.benchmarkId, top_n: state.topN },
        )
      : await fetchJson("/benchmark-mode-comparison", {
          benchmark_id: state.benchmarkId,
          top_n: state.topN,
        });
    if (requestId !== state.requestId) {
      return;
    }
    state.comparison = comparison;
    renderHero();
    renderModeComparison();
  } catch (error) {
    if (requestId !== state.requestId) {
      return;
    }
    setModeComparisonStatus(error.message);
  }
}

async function loadShortlist(requestId) {
  setShortlistStatus("Loading fused shortlist...");
  setExplanationStatus("Waiting for shortlist...");

  try {
    const shortlist = canUseMaterializedDetails()
      ? await fetchSnapshotJson(
          "/materialized/target-shortlist-explanations",
          "/target-shortlist-explanations",
          { benchmark_id: state.benchmarkId, mode: state.mode, top_n: state.topN },
        )
      : await fetchJson("/target-shortlist-explanations", {
          benchmark_id: state.benchmarkId,
          mode: state.mode,
          top_n: state.topN,
        });
    if (requestId !== state.requestId) {
      return;
    }

    state.shortlist = shortlist.items || [];
    if (!state.shortlist.length) {
      state.selectedGene = null;
      renderShortlist();
      setExplanationStatus("No target explanation available for this slice.");
      return;
    }

    const shortlistSymbols = new Set(state.shortlist.map((item) => item.gene_symbol));
    if (!state.selectedGene || !shortlistSymbols.has(state.selectedGene)) {
      state.selectedGene = state.shortlist[0].gene_symbol;
    }

    renderShortlist();
    await loadTargetExplanation();
  } catch (error) {
    if (requestId !== state.requestId) {
      return;
    }
    state.shortlist = [];
    renderShortlist();
    setExplanationStatus(error.message);
  }
}

async function loadDashboard() {
  const requestId = ++state.requestId;
  elements.refreshButton.disabled = true;

  await loadSnapshotSummary(requestId);
  await Promise.allSettled([loadModeComparison(requestId), loadShortlist(requestId)]);

  if (requestId === state.requestId) {
    elements.refreshButton.disabled = false;
  }
}

async function populateBenchmarks() {
  const payload = await fetchJson("/benchmarks");
  const options = payload.items || [];
  elements.benchmarkSelect.innerHTML = options
    .map((item) => `<option value="${item.benchmark_id}">${item.benchmark_id}</option>`)
    .join("");
  if (!state.benchmarkId && options[0]) {
    state.benchmarkId = options[0].benchmark_id;
  }
  if (state.benchmarkId) {
    elements.benchmarkSelect.value = state.benchmarkId;
  }
}

function bindEvents() {
  elements.apiBaseInput.addEventListener("change", () => {
    state.apiBase = elements.apiBaseInput.value.trim();
    state.dashboard = null;
    state.health = null;
    state.exportRows = null;
    state.comparison = null;
    state.shortlist = [];
    state.selectedGene = null;
    void initialize();
  });

  elements.benchmarkSelect.addEventListener("change", () => {
    state.benchmarkId = elements.benchmarkSelect.value;
    state.selectedGene = null;
    void loadDashboard();
  });

  elements.modeSelect.addEventListener("change", () => {
    state.mode = elements.modeSelect.value;
    state.selectedGene = null;
    void loadDashboard();
  });

  elements.topNInput.addEventListener("change", () => {
    state.topN = Number(elements.topNInput.value) || 10;
    state.selectedGene = null;
    void loadDashboard();
  });

  elements.refreshButton.addEventListener("click", () => {
    state.selectedGene = null;
    void loadDashboard();
  });
}

async function initialize() {
  state.apiBase = elements.apiBaseInput.value.trim();
  state.mode = elements.modeSelect.value;
  state.topN = Number(elements.topNInput.value) || 10;
  await populateBenchmarks();
  await loadDashboard();
}

bindEvents();
void initialize();
