let queues = [];
let selectedQueue = null;
let scripts = [];
let selectedScript = null;
let focusMode = "queues"; // "queues" | "scripts"

const queuePanel = document.getElementById("queue-panel");
const scriptPanel = document.getElementById("script-panel");
const launchBtn = document.getElementById("launch-btn");

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
  scriptPanel.innerHTML = "";
  scripts.forEach((item, i) => {
    const card = document.createElement("div");
    card.className = "card" + (selectedScript && selectedScript.script_id === item.script_id ? " selected" : "");
    card.dataset.index = i;
    card.textContent = item.script.title;
    card.addEventListener("click", () => selectScript(item));
    scriptPanel.appendChild(card);
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
  if (e.key === "Escape") {
    if (focusMode === "scripts") {
      focusMode = "queues";
      selectedScript = null;
      scripts = [];
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
    const cards = scriptPanel.querySelectorAll(".card");
    let idx = selectedScript ? scripts.findIndex((s) => s.script_id === selectedScript.script_id) : -1;
    if (e.key === "ArrowDown") idx = Math.min(idx + 1, scripts.length - 1);
    else if (e.key === "ArrowUp") idx = Math.max(idx - 1, 0);
    else if (e.key === "Enter" && idx >= 0) { selectScript(scripts[idx]); return; }
    else return;
    if (scripts[idx]) { selectedScript = scripts[idx]; renderScripts(); cards[idx]?.scrollIntoView({ block: "nearest" }); }
  }
});

loadQueues();
