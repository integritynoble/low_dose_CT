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
  board: null,        // raw board document (publication/receipt/gates)
  pub: null,          // board-level PublicationStatus view
  failedDiag: null,   // <path>.failed.json refused-save diagnostic, if any
};

const $ = (id) => document.getElementById(id);

/* ----------------------------------------------------------------------
 * Publication-state visibility (task 3, 2026-09-21).
 *
 * The page renders a *preview*: a pending/unverified receipt must never look
 * like a public result. State labels mirror scoring/verifier.py so the UI
 * and the CLI agree. A board is only reported PUBLISHED when
 * publication.referee_evidence is present — a submitter-controlled
 * `publication.status` flag is never treated as verification.
 * ---------------------------------------------------------------------- */
const PUBLISH_LABELS_ZH = {
  NO_CLAIM: "未发布 · 无声称",
  MISSING_LAYER: "未发布 · 缺层",
  INCOMPLETE: "未发布 · 不完整",
  REJECTED: "未发布 · 已拒绝",
  PUBLISHED: "已发布",
};

function publicationState(data, failedDiag) {
  const pub = (data && typeof data.publication === "object") ? data.publication : {};
  const receipt = data ? data.receipt : null;
  const hasPub = Object.keys(pub).length > 0;
  const hasReceipt = receipt && Object.keys(receipt).length > 0;
  const status = String(pub.status || "").toLowerCase();
  const ev = pub.referee_evidence;

  // 0) refused-save diagnostic next to the board (leaderboard.py writes
  //    <path>.failed.json when a save fails its submission gates)
  if (failedDiag && typeof failedDiag === "object" &&
      Array.isArray(failedDiag.gate_violations) && failedDiag.gate_violations.length) {
    return { state: "REJECTED", published: false, verified: false,
             detail: "refused save: " + failedDiag.gate_violations.join("; ") };
  }
  // 1) explicit refusal
  if (status === "rejected") {
    return { state: "REJECTED", published: false, verified: false,
             detail: "publication.status='rejected'; publication was refused" };
  }
  // 2) failed gates recorded on the artifact
  const failures = [];
  if (hasReceipt && receipt.gate && typeof receipt.gate === "object") {
    for (const [k, v] of Object.entries(receipt.gate)) {
      if (["FAIL", "INDETERMINATE"].includes(String(v).toUpperCase())) {
        failures.push(`receipt.gate.${k}=${v}`);
      }
    }
  }
  for (const block of ["trap_rank", "trap_rank_by_vendor"]) {
    const b = data ? data[block] : null;
    if (b && ["FAIL", "INDETERMINATE"].includes(b.verdict)) {
      failures.push(`${block}.verdict=${b.verdict}`);
    }
  }
  if (failures.length) {
    return { state: "REJECTED", published: false, verified: false,
             detail: "gate failure: " + failures.join("; ") };
  }
  // 3) no receipt / no publication block -> no claim
  if (!hasPub && !hasReceipt) {
    return { state: "NO_CLAIM", published: false, verified: false,
             detail: "board carries no receipt or publication; no publishable claim" };
  }
  // 4) PUBLISHED requires referee-verified evidence, never a submitter flag
  if (status === "published") {
    if (ev && ev.referee && ev.verified_at && ev.evidence_sha256) {
      return { state: "PUBLISHED", published: true, verified: true,
               detail: "published with referee-verified evidence" };
    }
    return { state: "INCOMPLETE", published: false, verified: false,
             detail: "status says 'published' but no referee-verified evidence; NOT treated as published" };
  }
  // 5) missing required vendor strata
  if (data && data.trap_rank_by_vendor && data.trap_rank_by_vendor.verdict === "MISSING_STRATUM") {
    return { state: "MISSING_LAYER", published: false, verified: false,
             detail: "missing required publication layer: vendor strata not fully covered" };
  }
  // 6) everything unfinished
  if (!status) {
    return { state: "INCOMPLETE", published: false, verified: false,
             detail: "receipt exists but publication block is missing/empty" };
  }
  return { state: "INCOMPLETE", published: false, verified: false,
           detail: `publication.status='${pub.status}'; not released` };
}

function entryPublication(entry) {
  if (entry.trap) {
    return { state: "NO_CLAIM", published: false, verified: false,
             label: "trap/控制", detail: "permanent control trap; not a publication object" };
  }
  if (entry.placeholder) {
    return { state: "NO_CLAIM", published: false, verified: false,
             label: "占位", detail: "placeholder; not a publication object" };
  }
  const b = state.pub || { state: "NO_CLAIM", published: false, verified: false };
  return { state: b.state, published: b.published, verified: b.verified,
           label: PUBLISH_LABELS_ZH[b.state] || b.state, detail: b.detail };
}

function renderPublicationBanner() {
  const banner = $("pub-banner");
  const p = state.pub;
  if (!p) { banner.hidden = true; return; }
  const stateKey = String(p.state).toLowerCase();
  banner.hidden = false;
  banner.className = "pub-banner pub-" + stateKey;
  const label = PUBLISH_LABELS_ZH[p.state] || p.state;
  const note = p.verified
    ? "此视图基于 referee 验证证据（非提交者自标 flag）。"
    : "当前为预览/未发布视图：收据不等于发布，待定或未验证内容不会标记为已发布。";
  banner.innerHTML =
    `<span class="pub-badge">${label}</span>` +
    `<span class="pub-detail">${escapeHtml(p.detail)}</span>` +
    `<span class="pub-note">${note}</span>`;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

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

/** 读取榜单：正式接口优先，回退到本地 JSON。保留完整 board 文档以便展示发布状态。 */
async function loadBoard() {
  for (const src of API_SOURCES) {
    try {
      const resp = await fetch(src, { headers: { Accept: "application/json" } });
      if (!resp.ok) continue;
      const data = await resp.json();
      const entries = Array.isArray(data) ? data : data.entries;
      if (!Array.isArray(entries)) continue;
      // A refused save keeps a <path>.failed.json beside the board; surface it
      // so the UI can label the board REJECTED instead of merely unclaimed.
      let failedDiag = null;
      try {
        const fr = await fetch(src + ".failed.json", { headers: { Accept: "application/json" } });
        if (fr.ok) failedDiag = await fr.json();
      } catch (err) {
        // 404 / CORS: no failed diagnostic; continue
      }
      return { source: src, entries, task: data.task || null, board: data, failedDiag };
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
    const pub = entryPublication(e);
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
    const tdPub = document.createElement("td");
    tdPub.className = "pub-cell";
    const badge = document.createElement("span");
    badge.className = "pub-badge pub-" + String(pub.state).toLowerCase();
    badge.textContent = pub.label;
    badge.title = pub.detail;
    tdPub.appendChild(badge);
    tr.appendChild(tdPub);
    tbody.appendChild(tr);
  });

  $("board").hidden = false;
  $("status").textContent =
    `共 ${rows.length} 条（数据源：${state.source}）` +
    (state.pub && state.pub.verified ? "；该榜单已由 referee 验证发布。" : "；当前为未发布/预览视图。");
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
    const { source, entries, task, board, failedDiag } = await loadBoard();
    state.entries = entries;
    state.source = source;
    state.board = board || null;
    state.failedDiag = failedDiag || null;
    state.pub = publicationState(board, state.failedDiag);
    if (task && task.label) $("task-label").textContent = task.label;
    renderPublicationBanner();

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
