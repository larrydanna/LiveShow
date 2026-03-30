let queues = [];
let selectedQueue = null;
let scripts = [];
let selectedScript = null;
let focusMode = "queues"; // "queues" | "scripts"

const queuePanel = document.getElementById("queue-panel");
const scriptPanel = document.getElementById("script-panel");
const launchBtn = document.getElementById("launch-btn");

async function applyInstanceName() {
  const cfg = await API.get("config");
  const name = cfg.instance_name || "LiveShow";
  document.getElementById("instance-name").textContent = name;
  document.title = `${name} – On Stage`;
}

async function loadQueues() {
  queues = await API.get("queues");
  renderQueues();
}

function renderQueues() {
  queuePanel.innerHTML = "";
  queues.forEach((q, i) => {
    const card = document.createElement("div");
    card.className = "card" + (selectedQueue && selectedQueue.id === q.id ? " selected" : "");
    card.dataset.index = i;
    card.textContent = q.name;
    card.addEventListener("click", () => selectQueue(q));
    queuePanel.appendChild(card);
  });
}

async function selectQueue(q) {
  selectedQueue = q;
  selectedScript = null;
  focusMode = "scripts";
  const detail = await API.get(`queues/${q.id}`);
  scripts = detail.scripts || [];
  renderQueues();
  renderScripts();
  launchBtn.disabled = true;
  await API.post("stage/state", { active_queue_id: q.id, active_script_id: null });
}

function renderScripts() {
  const filterInput = document.getElementById("script-filter");
  const filterWrap = document.getElementById("script-filter-wrap");
  const filterText = (filterInput ? filterInput.value : "").toLowerCase();
  const filtered = filterText
    ? scripts.filter((item) => item.script.title.toLowerCase().includes(filterText))
    : scripts;
  scriptPanel.innerHTML = "";
  // Show filter input only when there are scripts to display
  if (filterWrap) filterWrap.style.display = scripts.length > 0 ? "" : "none";
  filtered.forEach((item, i) => {
    const card = document.createElement("div");
    card.className = "card" + (selectedScript && selectedScript.script_id === item.script_id ? " selected" : "");
    card.dataset.index = scripts.findIndex((s) => s.script_id === item.script_id);
    card.textContent = item.script.title;
    card.addEventListener("click", () => selectScript(item));
    scriptPanel.appendChild(card);
  });
}

const scriptFilterInput = document.getElementById("script-filter");
const scriptFilterClear = document.getElementById("script-filter-clear");
if (scriptFilterInput) {
  scriptFilterInput.addEventListener("input", renderScripts);
}
if (scriptFilterClear) {
  scriptFilterClear.addEventListener("click", () => {
    scriptFilterInput.value = "";
    renderScripts();
  });
}

async function selectScript(item) {
  selectedScript = item;
  renderScripts();
  launchBtn.disabled = false;
  await API.post("stage/state", { active_script_id: item.script_id });
}

launchBtn.addEventListener("click", () => {
  if (selectedScript) {
    window.location.href = `/teleprompter?script_id=${selectedScript.script_id}`;
  }
});

document.addEventListener("keydown", (e) => {
  // Don't intercept keys when the script filter input is focused
  if (document.activeElement === scriptFilterInput) return;

  if (e.key === "Escape") {
    if (focusMode === "scripts") {
      focusMode = "queues";
      selectedScript = null;
      scripts = [];
      if (scriptFilterInput) scriptFilterInput.value = "";
      renderScripts();
      launchBtn.disabled = true;
    }
    return;
  }

  if (focusMode === "queues") {
    const cards = queuePanel.querySelectorAll(".card");
    let idx = selectedQueue ? queues.findIndex((q) => q.id === selectedQueue.id) : -1;
    if (e.key === "ArrowDown") idx = Math.min(idx + 1, queues.length - 1);
    else if (e.key === "ArrowUp") idx = Math.max(idx - 1, 0);
    else if (e.key === "Enter" && idx >= 0) { selectQueue(queues[idx]); return; }
    else return;
    if (queues[idx]) { selectedQueue = queues[idx]; renderQueues(); cards[idx]?.scrollIntoView({ block: "nearest" }); }
  } else {
    const filterText = scriptFilterInput ? scriptFilterInput.value.toLowerCase() : "";
    const visibleScripts = filterText
      ? scripts.filter((item) => item.script.title.toLowerCase().includes(filterText))
      : scripts;
    const cards = scriptPanel.querySelectorAll(".card");
    let idx = selectedScript ? visibleScripts.findIndex((s) => s.script_id === selectedScript.script_id) : -1;
    if (e.key === "ArrowDown") idx = Math.min(idx + 1, visibleScripts.length - 1);
    else if (e.key === "ArrowUp") idx = Math.max(idx - 1, 0);
    else if (e.key === "Enter" && idx >= 0) { selectScript(visibleScripts[idx]); return; }
    else return;
    if (visibleScripts[idx]) { selectedScript = visibleScripts[idx]; renderScripts(); cards[idx]?.scrollIntoView({ block: "nearest" }); }
  }
});

loadQueues();
applyInstanceName();

// Poll stage state for remote-triggered teleprompter launch
const STAGE_POLL_INTERVAL_MS = 2000;
let launchInProgress = false;
const stagePollId = setInterval(async () => {
  if (launchInProgress) return;
  const state = await API.get("stage/state");
  if (state.launch_teleprompter && state.active_script_id) {
    launchInProgress = true;
    clearInterval(stagePollId);
    await API.post("stage/state", { launch_teleprompter: false });
    window.location.href = `/teleprompter?script_id=${state.active_script_id}`;
  }
}, STAGE_POLL_INTERVAL_MS);
