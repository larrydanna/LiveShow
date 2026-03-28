const PAGE_SCROLL_AMOUNT = 600;
const STATE_POLL_INTERVAL_MS = 3000;

// ---- State ----
let allScripts = [];
let allQueues = [];

// ---- Tab switching ----
document.querySelectorAll(".nav-link[data-tab]").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".nav-link[data-tab]").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("show", "active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("show", "active");
  });
});

// ---- Scripts Tab ----
async function loadScripts() {
  allScripts = await API.get("scripts");
  renderScriptsList();
  populateScriptDropdowns();
}

function renderScriptsList() {
  const list = document.getElementById("scripts-list");
  list.innerHTML = "";
  allScripts.forEach((s) => {
    const row = document.createElement("div");
    row.className = "list-group-item d-flex justify-content-between align-items-center";
    row.innerHTML = `<span><strong>${escHtml(s.title)}</strong> <small class="text-muted">by ${escHtml(s.submitted_by)}</small></span>
      <button class="btn btn-sm btn-danger" data-id="${s.id}">Delete</button>`;
    row.querySelector("button").addEventListener("click", async () => {
      await API.delete(`scripts/${s.id}`);
      loadScripts();
    });
    list.appendChild(row);
  });
}

document.getElementById("add-script-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  await API.post("scripts", { title: fd.get("title"), body: fd.get("body"), submitted_by: fd.get("submitted_by") });
  e.target.reset();
  loadScripts();
});

// ---- Queues Tab ----
async function loadQueues() {
  allQueues = await API.get("queues");
  renderQueuesList();
  populateScriptDropdowns();
}

function renderQueuesList() {
  const container = document.getElementById("queues-list");
  container.innerHTML = "";
  allQueues.forEach((q) => {
    const card = document.createElement("div");
    card.className = "card mb-3";
    card.innerHTML = `
      <div class="card-header d-flex justify-content-between align-items-center">
        <strong id="qname-${q.id}">${escHtml(q.name)}</strong>
        <div>
          <button class="btn btn-sm btn-outline-secondary me-1 btn-rename" data-id="${q.id}">Rename</button>
          <button class="btn btn-sm btn-danger btn-delete-queue" data-id="${q.id}">Delete</button>
        </div>
      </div>
      <div class="card-body">
        <div id="qscripts-${q.id}" class="mb-2"></div>
        <div class="input-group input-group-sm">
          <select class="form-select select-add-script" data-qid="${q.id}"></select>
          <input type="number" class="form-control input-position" placeholder="Position" style="max-width:90px" value="0">
          <button class="btn btn-outline-primary btn-add-to-queue" data-qid="${q.id}">Add Script</button>
        </div>
      </div>`;
    container.appendChild(card);
    renderQueueScripts(q.id);
    card.querySelector(".btn-rename").addEventListener("click", () => renameQueue(q.id));
    card.querySelector(".btn-delete-queue").addEventListener("click", async () => {
      await API.delete(`queues/${q.id}`);
      loadQueues();
    });
    card.querySelector(".btn-add-to-queue").addEventListener("click", async () => {
      const sel = card.querySelector(".select-add-script");
      const pos = card.querySelector(".input-position");
      if (!sel.value) return;
      await API.post(`queues/${q.id}/scripts`, { script_id: parseInt(sel.value), position: parseInt(pos.value) || 0 });
      renderQueueScripts(q.id);
    });
  });
  populateScriptDropdowns();
}

async function renderQueueScripts(queueId) {
  const detail = await API.get(`queues/${queueId}`);
  const el = document.getElementById(`qscripts-${queueId}`);
  if (!el) return;
  el.innerHTML = "";
  detail.scripts.forEach((item, i) => {
    const row = document.createElement("div");
    row.className = "d-flex align-items-center gap-1 mb-1";
    row.innerHTML = `<span class="flex-grow-1">${i + 1}. ${escHtml(item.script.title)}</span>
      <button class="btn btn-sm btn-outline-secondary btn-up" data-qid="${queueId}" data-sid="${item.script_id}" data-pos="${item.position}" data-i="${i}">▲</button>
      <button class="btn btn-sm btn-outline-secondary btn-down" data-qid="${queueId}" data-sid="${item.script_id}" data-pos="${item.position}" data-i="${i}">▼</button>
      <button class="btn btn-sm btn-outline-danger btn-rm" data-qid="${queueId}" data-sid="${item.script_id}">✕</button>`;
    row.querySelector(".btn-rm").addEventListener("click", async () => {
      await API.delete(`queues/${queueId}/scripts/${item.script_id}`);
      renderQueueScripts(queueId);
    });
    row.querySelector(".btn-up").addEventListener("click", async () => {
      if (i === 0) return;
      const reorder = detail.scripts.map((s, j) => {
        let pos = j;
        if (j === i) pos = i - 1;
        else if (j === i - 1) pos = i;
        return { script_id: s.script_id, position: pos };
      });
      await API.put(`queues/${queueId}/scripts/reorder`, reorder);
      renderQueueScripts(queueId);
    });
    row.querySelector(".btn-down").addEventListener("click", async () => {
      if (i === detail.scripts.length - 1) return;
      const reorder = detail.scripts.map((s, j) => {
        let pos = j;
        if (j === i) pos = i + 1;
        else if (j === i + 1) pos = i;
        return { script_id: s.script_id, position: pos };
      });
      await API.put(`queues/${queueId}/scripts/reorder`, reorder);
      renderQueueScripts(queueId);
    });
    el.appendChild(row);
  });
}

async function renameQueue(queueId) {
  const nameEl = document.getElementById(`qname-${queueId}`);
  const newName = prompt("New queue name:", nameEl.textContent);
  if (newName && newName.trim()) {
    await API.put(`queues/${queueId}`, { name: newName.trim() });
    loadQueues();
  }
}

document.getElementById("add-queue-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("new-queue-name").value.trim();
  if (!name) return;
  await API.post("queues", { name });
  e.target.reset();
  loadQueues();
});

function populateScriptDropdowns() {
  document.querySelectorAll(".select-add-script").forEach((sel) => {
    const currentVal = sel.value;
    sel.innerHTML = `<option value="">-- Select script --</option>` +
      allScripts.map((s) => `<option value="${s.id}">${escHtml(s.title)}</option>`).join("");
    if (currentVal) sel.value = currentVal;
  });
  const stageQueueSel = document.getElementById("stage-queue-select");
  const stageScriptSel = document.getElementById("stage-script-select");
  if (stageQueueSel) {
    stageQueueSel.innerHTML = `<option value="">-- None --</option>` +
      allQueues.map((q) => `<option value="${q.id}">${escHtml(q.name)}</option>`).join("");
  }
  if (stageScriptSel) {
    stageScriptSel.innerHTML = `<option value="">-- None --</option>` +
      allScripts.map((s) => `<option value="${s.id}">${escHtml(s.title)}</option>`).join("");
  }
}

// ---- Stage Control Tab ----
async function loadStageState() {
  const state = await API.get("stage/state");
  const qSel = document.getElementById("stage-queue-select");
  const sSel = document.getElementById("stage-script-select");
  const speedSlider = document.getElementById("stage-speed-slider");
  const speedVal = document.getElementById("stage-speed-val");
  const scrollingBtn = document.getElementById("stage-scroll-toggle");
  const launchBtn = document.getElementById("stage-launch-btn");
  if (state.active_queue_id) qSel.value = state.active_queue_id;
  if (state.active_script_id) sSel.value = state.active_script_id;
  speedSlider.value = state.auto_scroll_speed;
  speedVal.textContent = state.auto_scroll_speed;
  scrollingBtn.textContent = state.is_scrolling ? "Stop Scrolling" : "Start Scrolling";
  scrollingBtn.className = "btn " + (state.is_scrolling ? "btn-warning" : "btn-success");
  launchBtn.disabled = !state.active_script_id;
}

document.getElementById("stage-queue-select").addEventListener("change", async (e) => {
  await API.post("stage/state", { active_queue_id: e.target.value ? parseInt(e.target.value) : null });
});
document.getElementById("stage-script-select").addEventListener("change", async (e) => {
  await API.post("stage/state", { active_script_id: e.target.value ? parseInt(e.target.value) : null });
  document.getElementById("stage-launch-btn").disabled = !e.target.value;
});
document.getElementById("stage-speed-slider").addEventListener("input", async (e) => {
  document.getElementById("stage-speed-val").textContent = e.target.value;
  await API.post("stage/state", { auto_scroll_speed: parseFloat(e.target.value) });
});
document.getElementById("stage-scroll-toggle").addEventListener("click", async () => {
  const state = await API.get("stage/state");
  const newState = !state.is_scrolling;
  await API.post("stage/state", { is_scrolling: newState });
  loadStageState();
});
document.getElementById("stage-page-up").addEventListener("click", async () => {
  const state = await API.get("stage/state");
  await API.post("stage/state", { scroll_position: Math.max(0, state.scroll_position - PAGE_SCROLL_AMOUNT) });
});
document.getElementById("stage-page-down").addEventListener("click", async () => {
  const state = await API.get("stage/state");
  await API.post("stage/state", { scroll_position: state.scroll_position + PAGE_SCROLL_AMOUNT });
});
document.getElementById("stage-launch-btn").addEventListener("click", async () => {
  await API.post("stage/state", { launch_teleprompter: true });
});

function escHtml(str) {
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// ---- Export ----
document.getElementById("export-btn").addEventListener("click", () => {
  window.location.href = "/api/export";
});

// ---- Import ----
let _importReport = null;

document.getElementById("import-btn").addEventListener("click", () => {
  document.getElementById("import-file-input").click();
});

document.getElementById("import-file-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  e.target.value = ""; // reset so the same file can be chosen again

  const overlay = document.getElementById("import-overlay");
  const summaryEl = document.getElementById("import-summary");
  const detailWrap = document.getElementById("import-detail-wrap");
  const detailEl = document.getElementById("import-detail");

  summaryEl.innerHTML = '<span style="color:#6c757d;">⏳ Importing…</span>';
  detailWrap.style.display = "none";
  overlay.style.display = "flex";

  try {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/import", { method: "POST", body: fd });
    const report = await res.json();
    if (!res.ok) {
      summaryEl.innerHTML = `<span style="color:#842029;">❌ Import failed: ${escHtml(report.detail || JSON.stringify(report))}</span>`;
      _importReport = null;
      return;
    }
    _importReport = report;
    const s = report.summary;
    summaryEl.innerHTML = `
      <p style="margin:0 0 0.5rem;">
        <strong>File:</strong> ${escHtml(report.source_filename)}
      </p>
      <table style="border-collapse:collapse; font-size:0.9rem;">
        <thead><tr>
          <th style="padding:0.25rem 0.75rem 0.25rem 0; text-align:left;">Type</th>
          <th style="padding:0.25rem 0.5rem; text-align:right; color:#198754;">Imported</th>
          <th style="padding:0.25rem 0.5rem; text-align:right; color:#856404;">Skipped</th>
          <th style="padding:0.25rem 0.5rem; text-align:right; color:#842029;">Failed</th>
        </tr></thead>
        <tbody>
          <tr>
            <td style="padding:0.2rem 0.75rem 0.2rem 0;">Scripts</td>
            <td style="padding:0.2rem 0.5rem; text-align:right;">${s.scripts.imported}</td>
            <td style="padding:0.2rem 0.5rem; text-align:right;">${s.scripts.skipped}</td>
            <td style="padding:0.2rem 0.5rem; text-align:right;">${s.scripts.failed}</td>
          </tr>
          <tr>
            <td style="padding:0.2rem 0.75rem 0.2rem 0;">Queues</td>
            <td style="padding:0.2rem 0.5rem; text-align:right;">${s.queues.imported}</td>
            <td style="padding:0.2rem 0.5rem; text-align:right;">${s.queues.skipped}</td>
            <td style="padding:0.2rem 0.5rem; text-align:right;">${s.queues.failed}</td>
          </tr>
          <tr>
            <td style="padding:0.2rem 0.75rem 0.2rem 0;">Queue Items</td>
            <td style="padding:0.2rem 0.5rem; text-align:right;">${s.queue_items.imported}</td>
            <td style="padding:0.2rem 0.5rem; text-align:right;">${s.queue_items.skipped}</td>
            <td style="padding:0.2rem 0.5rem; text-align:right;">${s.queue_items.failed}</td>
          </tr>
        </tbody>
      </table>
      <p style="margin:0.5rem 0 0; font-size:0.85rem; color:#6c757d;">
        Stage state: ${escHtml(s.stage_state)}
      </p>`;

    detailEl.textContent = JSON.stringify(report.details, null, 2);
    loadScripts();
    loadQueues();
  } catch (err) {
    summaryEl.innerHTML = `<span style="color:#842029;">❌ ${escHtml(err.message)}</span>`;
    _importReport = null;
  }
});

document.getElementById("import-view-details").addEventListener("click", () => {
  const w = document.getElementById("import-detail-wrap");
  const btn = document.getElementById("import-view-details");
  const visible = w.style.display !== "none";
  w.style.display = visible ? "none" : "block";
  btn.textContent = visible ? "View Details" : "Hide Details";
});

document.getElementById("import-download-report").addEventListener("click", () => {
  if (!_importReport) return;
  const blob = new Blob([JSON.stringify(_importReport, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const now = new Date();
  const ts = now.toISOString().slice(0, 19).replace("T", "_").replace(/:/g, "");
  a.download = `import_report_${ts}.json`;
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById("import-close").addEventListener("click", () => {
  document.getElementById("import-overlay").style.display = "none";
});

// ---- Settings Tab ----
async function loadSettings() {
  try {
    const cfg = await API.get("config");
    document.getElementById("instance-name-input").value = cfg.instance_name || "LiveShow";
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}

document.getElementById("settings-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const newName = document.getElementById("instance-name-input").value.trim();
  const alertEl = document.getElementById("settings-alert");
  try {
    await API.put("config", { instance_name: newName });
    alertEl.className = "alert alert-success";
    alertEl.textContent = "Settings saved.";
    alertEl.style.display = "block";
    setTimeout(() => { alertEl.style.display = "none"; }, 3000);
  } catch (err) {
    alertEl.className = "alert alert-danger";
    alertEl.textContent = "Failed to save settings: " + err.message;
    alertEl.style.display = "block";
  }
});

// Init
loadScripts();
loadQueues();
loadStageState();
setInterval(loadStageState, STATE_POLL_INTERVAL_MS);
loadSettings();
