const SCROLL_SYNC_THRESHOLD = 5;
const SCROLL_POST_THROTTLE_MS = 500;
const STATE_POLL_INTERVAL_MS = 2000;
const params = new URLSearchParams(window.location.search);

const titleEl = document.getElementById("script-title");
const bodyEl = document.getElementById("script-body");
const startStopBtn = document.getElementById("start-stop-btn");
const speedSlider = document.getElementById("speed-slider");
const speedVal = document.getElementById("speed-val");

let isScrolling = false;
let scrollSpeed = 3;
let rafId = null;
let lastTime = null;
let currentScriptId = params.get("script_id") ? parseInt(params.get("script_id"), 10) : null;

async function loadScript(id) {
  if (!id) { titleEl.textContent = "No script selected"; bodyEl.textContent = ""; return; }
  const [script, cfg] = await Promise.all([
    API.get(`scripts/${id}`),
    API.get("config"),
  ]);
  titleEl.textContent = script.title;
  bodyEl.textContent = script.body;
  const instanceName = cfg.instance_name || "LiveShow";
  document.title = `${instanceName} – Teleprompter`;
}

function getPixelsPerSecond() {
  // speed 1-10 maps to 20-200 px/s
  return scrollSpeed * 20;
}

function scrollStep(ts) {
  if (!isScrolling) return;
  if (lastTime === null) lastTime = ts;
  const delta = (ts - lastTime) / 1000;
  lastTime = ts;
  bodyEl.parentElement.scrollTop += getPixelsPerSecond() * delta;
  postScrollState();
  rafId = requestAnimationFrame(scrollStep);
}

function startScroll() {
  isScrolling = true;
  lastTime = null;
  startStopBtn.textContent = "Stop";
  rafId = requestAnimationFrame(scrollStep);
  API.post("stage/state", { is_scrolling: true });
}

function stopScroll() {
  isScrolling = false;
  lastTime = null;
  startStopBtn.textContent = "Start";
  if (rafId) cancelAnimationFrame(rafId);
  API.post("stage/state", { is_scrolling: false });
}

let postThrottle = 0;
function postScrollState() {
  const now = Date.now();
  if (now - postThrottle > SCROLL_POST_THROTTLE_MS) {
    postThrottle = now;
    API.post("stage/state", { scroll_position: bodyEl.parentElement.scrollTop });
  }
}

startStopBtn.addEventListener("click", () => {
  if (isScrolling) stopScroll(); else startScroll();
});

speedSlider.addEventListener("input", () => {
  scrollSpeed = parseFloat(speedSlider.value);
  speedVal.textContent = scrollSpeed;
  API.post("stage/state", { auto_scroll_speed: scrollSpeed });
});

document.addEventListener("keydown", (e) => {
  const scroller = bodyEl.parentElement;
  if (e.key === " ") { e.preventDefault(); if (isScrolling) stopScroll(); else startScroll(); }
  else if (e.key === "ArrowDown") { e.preventDefault(); scroller.scrollTop += 50; }
  else if (e.key === "ArrowUp") { e.preventDefault(); scroller.scrollTop -= 50; }
  else if (e.key === "PageDown") { e.preventDefault(); scroller.scrollTop += scroller.clientHeight; }
  else if (e.key === "PageUp") { e.preventDefault(); scroller.scrollTop -= scroller.clientHeight; }
  else if (e.key === "Escape") { stopScroll(); window.location.href = "/"; }
});

document.getElementById("page-up-btn").addEventListener("click", () => {
  bodyEl.parentElement.scrollTop -= bodyEl.parentElement.clientHeight;
});
document.getElementById("page-down-btn").addEventListener("click", () => {
  bodyEl.parentElement.scrollTop += bodyEl.parentElement.clientHeight;
});
document.getElementById("back-btn").addEventListener("click", () => {
  stopScroll();
  window.location.href = "/";
});

// Poll stage state every 2 seconds and sync from remote
setInterval(async () => {
  const state = await API.get("stage/state");
  const scroller = bodyEl.parentElement;

  // Reload script content if the remote has selected a different script
  const remoteScriptId = state.active_script_id ? parseInt(state.active_script_id, 10) : null;
  if (remoteScriptId && remoteScriptId !== currentScriptId) {
    currentScriptId = remoteScriptId;
    stopScroll();
    scroller.scrollTop = 0;
    await loadScript(currentScriptId);
    await API.post("stage/state", { scroll_position: 0 });
  }

  if (!isScrolling && typeof state.scroll_position === 'number' &&
      Math.abs(scroller.scrollTop - state.scroll_position) > SCROLL_SYNC_THRESHOLD) {
    scroller.scrollTop = state.scroll_position;
  }
  if (state.auto_scroll_speed !== scrollSpeed) {
    scrollSpeed = state.auto_scroll_speed;
    speedSlider.value = scrollSpeed;
    speedVal.textContent = scrollSpeed;
  }
  if (state.is_scrolling && !isScrolling) startScroll();
  else if (!state.is_scrolling && isScrolling) stopScroll();
}, STATE_POLL_INTERVAL_MS);

// Load initial script, then reset the remote launch flag
(async () => {
  await loadScript(currentScriptId);
  try {
    await API.post("stage/state", { launch_teleprompter: false });
  } catch (_) {
    // Best-effort reset; non-critical if it fails
  }
})();
