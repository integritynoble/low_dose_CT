/* WS-4 Leaderboard public front-end (Phase 1 / 1.3, static placeholder).
 *
 * Data interface: the page prefers the future scoring API endpoint
 * `/api/leaderboard` (placeholder — 404 today) and falls back to the local
 * board file `../scoring/data/leaderboard.json`. Swap `API_SOURCES` for the
 * real endpoint once the scoring service is wired (see web/README.md).
 */
"use strict";

/** 数据源候选：正式接口占位优先，本地文件回退 */
const API_SOURCES = [
  "/api/leaderboard",
  "../scoring/data/leaderboard.json",
];

/** 展示用指标列（键 -> 表头） */
const METRIC_COLUMNS = {
  bander_roi: "BANDER ROI",
  bander_full: "BANDER Full",
  roi_tm_auc: "ROI TM AUC",
  cnr_mean: "CNR",
  cho_auc_mean: "CHO AUC",
  npwe_mean: "NPWE",
  psnr_db: "PSNR (dB)",
  ssim: "SSIM",
};

/** 默认排序指标：ROI 检测能量，降序（高在前，trap 垫底） */
const DEFAULT_METRIC = "bander_roi";

const state = {
  entries: [],
  metric: DEFAULT_METRIC,
  order: "desc",
  vendor: "",
  dose: "",
  year: "",
  source: null,
};

const $ = (id) => document.getElementById(id);

function fmtNum(value) {
  if (value === null || value === undefined || value === "") return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return n.toLocaleString("en-US", { maximumFractionDigits: 4 });
}

function yearOf(entry) {
  const t = entry && entry.submitted_at;
  if (!t) return "";
  const m = String(t).match(/\d{4}/);
  return m ? m[0] : "";
}

/** 读取榜单：正式接口优先，回退到本地 JSON。 */
async function loadBoard() {
  for (const src of API_SOURCES) {
    try {
      const resp = await fetch(src, { headers: { Accept: "application/json" } });
      if (!resp.ok) continue;
      const data = await resp.json();
      const entries = Array.isArray(data) ? data : data.entries;
      if (!Array.isArray(entries)) continue;
      return { source: src, entries, task: data.task || null };
    } catch (err) {
      // 该数据源不可用，尝试下一个
    }
  }
  throw new Error("没有可用的排行榜数据源");
}

function uniqueSorted(values) {
  return [...new Set(values.filter((v) => v !== null && v !== "" && v !== undefined))].sort();
}

function fillSelect(select, values, placeholder) {
  select.innerHTML = "";
  if (placeholder !== undefined) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    select.appendChild(opt);
  }
  for (const v of values) {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    select.appendChild(opt);
  }
}

function metricValue(entry, key) {
  const m = entry.metrics || {};
  return m[key];
}

function applyFiltersAndSort() {
  let rows = state.entries.slice();
  if (state.vendor) rows = rows.filter((e) => (e.vendor || "") === state.vendor);
  if (state.dose) rows = rows.filter((e) => (e.dose || "") === state.dose);
  if (state.year) rows = rows.filter((e) => yearOf(e) === state.year);

  const dir = state.order === "desc" ? -1 : 1;
  rows.sort((a, b) => {
    const va = metricValue(a, state.metric);
    const vb = metricValue(b, state.metric);
    if (va === null || va === undefined || va === "") return 1; // 缺值垫底
    if (vb === null || vb === undefined || vb === "") return -1;
    const d = (Number(va) - Number(vb)) * dir;
    if (d !== 0) return d;
    return String(a.method || a.id).localeCompare(String(b.method || b.id));
  });
  return rows;
}

function render() {
  const rows = applyFiltersAndSort();
  const tbody = $("board-body");
  tbody.innerHTML = "";
  $("th-metric").textContent = (METRIC_COLUMNS[state.metric] || state.metric) + " (排序)";

  rows.forEach((e, i) => {
    const tr = document.createElement("tr");
    if (e.trap) tr.classList.add("row-trap");
    const m = e.metrics || {};
    const cells = [
      String(i + 1),
      e.method || e.id || "—",
      e.vendor || "—",
      e.dose || "—",
      fmtNum(m[state.metric]),
      fmtNum(m.psnr_db),
      fmtNum(m.ssim),
      fmtNum(m.cnr_mean),
      fmtNum(m.cho_auc_mean),
      fmtNum(m.bander_roi),
      fmtNum(m.bander_full),
      fmtNum(m.roi_tm_auc),
      e.submitted_at ? String(e.submitted_at).slice(0, 10) : "—",
      e.trap ? "trap" : (e.kind || "submission"),
    ];
    cells.forEach((text) => {
      const td = document.createElement("td");
      td.textContent = text;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  $("board").hidden = false;
  $("status").textContent =
    `共 ${rows.length} 条（数据源：${state.source}）`;
}

function bindControls() {
  $("metric").addEventListener("change", (e) => { state.metric = e.target.value; render(); });
  $("order").addEventListener("change", (e) => { state.order = e.target.value; render(); });
  $("vendor").addEventListener("change", (e) => { state.vendor = e.target.value; render(); });
  $("dose").addEventListener("change", (e) => { state.dose = e.target.value; render(); });
  $("year").addEventListener("change", (e) => { state.year = e.target.value; render(); });
  $("reset").addEventListener("click", () => {
    state.metric = DEFAULT_METRIC;
    state.order = "desc";
    state.vendor = "";
    state.dose = "";
    state.year = "";
    $("metric").value = DEFAULT_METRIC;
    $("order").value = "desc";
    $("vendor").value = "";
    $("dose").value = "";
    $("year").value = "";
    render();
  });
}

async function init() {
  try {
    const { source, entries, task } = await loadBoard();
    state.entries = entries;
    state.source = source;
    if (task && task.label) $("task-label").textContent = task.label;

    fillSelect($("metric"), Object.keys(METRIC_COLUMNS).filter((k) =>
      entries.some((e) => (e.metrics || {})[k] !== undefined)), "全部");
    if (![...$("metric").options].some((o) => o.value === DEFAULT_METRIC)) {
      $("metric").insertAdjacentHTML("afterbegin",
        `<option value="${DEFAULT_METRIC}">${METRIC_COLUMNS[DEFAULT_METRIC]}</option>`);
    }
    $("metric").value = DEFAULT_METRIC;
    fillSelect($("vendor"), uniqueSorted(entries.map((e) => e.vendor)), "全部");
    fillSelect($("dose"), uniqueSorted(entries.map((e) => e.dose)), "全部");
    fillSelect($("year"), uniqueSorted(entries.map(yearOf)), "全部");
    bindControls();
    render();
  } catch (err) {
    $("status").textContent = "加载失败：" + err.message;
  }
}

init();
