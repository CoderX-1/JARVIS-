"use strict";
const token = document.querySelector('meta[name="session-token"]').content;
const $ = (id) => document.getElementById(id);
let lastEvents = "";
let lastOverview = null;
let busy = false;
let polling = false;
let currentView = "board";
let lastHealth = {};
let lastActivity = "";
let lastAbilities = "";
let lastFiles = "";
let pendingRecycleId = "";

async function api(path, body) {
  const options = {headers: {"X-Jarvis-Session": token}, cache: "no-store"};
  if (body !== undefined) {
    options.method = "POST";
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

function setText(id, value) { $(id).textContent = String(value ?? ""); }
function clear(node) { node.replaceChildren(); }
function element(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = String(value);
  return node;
}
function showError(message) { setText("formError", message); $("formError").hidden = !message; }
function clock(value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], {hour:"2-digit", minute:"2-digit", second:"2-digit"});
}

function switchView(view) {
  if (!$("view-" + view)) return;
  currentView = view;
  for (const tab of document.querySelectorAll(".view-tab")) {
    const selected = tab.dataset.view === view;
    tab.classList.toggle("selected", selected);
    if (selected) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  }
  for (const pane of document.querySelectorAll(".view")) {
    pane.hidden = pane.id !== "view-" + view;
  }
  if (view === "abilities" && lastOverview) renderAbilities(lastOverview.capabilities || []);
  if (view === "activity" && lastOverview) renderActivity(lastOverview);
  if (view === "files" && lastOverview) renderFiles(lastOverview);
  if (view === "devices") { refreshMics(); refreshCameras(); }
}

async function refreshMics() {
  const select = $("micSelect");
  try {
    const data = await api("/api/devices");
    const chosen = data.selected || "";
    select.replaceChildren(new Option("System default", ""));
    for (const input of data.inputs || []) select.add(new Option(`${input.name} · ${input.host}`, input.id));
    select.value = chosen;
    setText("micFeedback", chosen && select.value !== chosen
      ? "Saved mic uses an old partial name or is disconnected. Choose a precise input here."
      : `${(data.inputs || []).length} input source(s) found. ${chosen ? "Saved microphone selected." : "Using system default."}`);
  } catch (error) { setText("micFeedback", error.message); }
}

async function refreshCameras() {
  const select = $("cameraSelect");
  if (!navigator.mediaDevices?.enumerateDevices) {
    setText("cameraFeedback", "Camera listing is unavailable in this WebView.");
    return;
  }
  try {
    const cameras = (await navigator.mediaDevices.enumerateDevices()).filter(device => device.kind === "videoinput");
    const selected = new URLSearchParams(location.search).get("spatialCam") || "";
    select.replaceChildren(new Option("System default", ""));
    cameras.forEach((device, index) => select.add(new Option(device.label || `Camera ${index + 1}`, device.deviceId)));
    select.value = selected;
    setText("cameraFeedback", cameras.length
      ? `${cameras.length} camera(s) found. Names may require camera access first.`
      : "No camera detected. Spatial preview still works without one.");
  } catch (error) { setText("cameraFeedback", error.message); }
}

function spatialStatus(available) {
  if (!available) return "Spatial service offline";
  const status = $("spatialMount").dataset.status;
  if (status === "camera-error") return "Camera unavailable — use preview";
  if (status === "tracking") return "Hand tracking active";
  if (status === "preview") return "Mouse mode — camera off";
  return "Spatial starting";
}

function renderHealth(health) {
  lastHealth = health;
  const connected = !!health.brain;
  const badge = $("connection");
  badge.classList.toggle("online", connected);
  badge.classList.toggle("offline", !connected);
  setText("connectionText", connected ? "Brain connected" : "Brain offline");
  const state = health.visualizer ? health.state : "offline";
  setText("voiceState", "Voice " + state);
  const spatial = spatialStatus(!!health.hands);
  setText("spatialState", spatial);
  setText("spatialVoiceState", spatial);
  setText("turnState", connected ? state : "Offline");
  $("boardOffline").hidden = !!health.visualizer;
  $("boardMount").hidden = !health.visualizer;
  $("spatialOffline").hidden = !!health.hands;
  $("spatialMount").hidden = !health.hands;
  $("spatialCamera").hidden = !health.hands;
  $("spatialCamera").textContent = new URLSearchParams(location.search).get("spatialCamera") === "1"
    ? "Use camera-free preview" : "Try hand tracking";
}

function renderEvents(events) {
  const signature = JSON.stringify(events);
  if (signature === lastEvents) return;
  lastEvents = signature;
  const box = $("messages");
  clear(box);
  if (!events.length) {
    box.append(element("p", "empty-chat", "Talk with HOME or type a mission below. Both use the same JARVIS session."));
    return;
  }
  for (const event of events.slice(-80)) {
    if (!event || typeof event !== "object") continue;
    const role = event.kind === "user" ? "user" : "assistant";
    const card = element("article", "message " + role);
    const meta = element("div", "message-meta");
    meta.append(element("span", "", role === "user" ? "You" : event.kind === "error" ? "System" : "JARVIS"));
    meta.append(element("time", "", clock(Number(event.ts || 0) * 1000)));
    card.append(meta, element("p", "", event.text || ""));
    box.append(card);
  }
  box.scrollTop = box.scrollHeight;
}

function renderActivity(overview) {
  const signature = JSON.stringify([overview.task, overview.audit]);
  if (signature === lastActivity) return;
  lastActivity = signature;
  const task = overview.task;
  const summary = $("taskSummary");
  clear(summary);
  if (task && Array.isArray(task.steps)) {
    summary.append(element("strong", "", "Task: " + task.status));
    for (const step of task.steps) summary.append(element("p", "", `${step.id}. ${step.description} — ${step.status}`));
  } else summary.textContent = "No task plan yet.";
  const list = $("activityList");
  clear(list);
  const audit = Array.isArray(overview.audit) ? overview.audit : [];
  if (!audit.length) { list.append(element("p", "quiet", "No recent tool verification records.")); return; }
  for (const item of audit.slice().reverse()) {
    const row = element("article", "activity-item");
    row.append(element("strong", "", item.tool || "Tool"), element("span", "status " + (item.status || "unknown"), item.status || "unknown"));
    row.append(element("time", "", clock(item.timestamp)), element("small", "", item.goal_verified ? "Goal verified" : "Goal not verified"));
    list.append(row);
  }
}

function renderAbilities(abilities) {
  const query = $("abilitySearch").value.trim().toLowerCase();
  const signature = JSON.stringify([abilities, query]);
  if (signature === lastAbilities) return;
  lastAbilities = signature;
  const found = abilities.filter((item) => (item.name + " " + item.description).toLowerCase().includes(query));
  setText("abilitySummary", `${found.length} of ${abilities.length} registered tools. Availability is checked when used.`);
  const list = $("abilitiesList"); clear(list);
  if (!found.length) { list.append(element("p", "quiet", "No matching registered tools.")); return; }
  for (const item of found) {
    const card = element("article", "ability-item");
    card.append(element("strong", "", item.name || "Unnamed tool"));
    card.append(element("p", "", item.description || "No description in registry."));
    list.append(card);
  }
}

function renderFiles(overview) {
  const canCreateDeck = (overview.capabilities || []).some((item) => item.name === "professional_topic_presentation");
  $("preparePresentation").hidden = !canCreateDeck;
  $("presentationHint").hidden = !canCreateDeck;
  const signature = JSON.stringify([overview.files, overview.apps]);
  if (signature === lastFiles) return;
  lastFiles = signature;
  const reports = $("reportsList"); clear(reports);
  const files = Array.isArray(overview.files) ? overview.files : [];
  if (!files.length) reports.append(element("p", "quiet", "No reports or presentations on the output shelf."));
  for (const file of files) {
    const row = element("article", "file-item");
    const label = element("div", "file-details");
    label.append(element("strong", "", file.name));
    const format = String(file.name || "").split(".").pop().toUpperCase();
    const date = Number.isFinite(Number(file.modified)) ? new Date(file.modified * 1000).toLocaleString() : "";
    label.append(element("p", "", `${format}  ·  ${format === "PPTX" ? "Presentation" : "Report"}  ·  ${Math.max(1, Math.round((file.bytes || 0) / 1024))} KB${date ? "  ·  " + date : ""}`));
    const actions = element("div", "file-actions");
    const button = element("button", "", "Open");
    button.type = "button";
    button.addEventListener("click", async () => {
      try { await api("/api/open-report", {id:file.id, version:file.version}); showError(""); }
      catch (error) { showError(error.message); }
    });
    actions.append(button);
    if (pendingRecycleId === file.id) {
      const confirm = element("button", "recycle-confirm", "Move to Recycle Bin");
      confirm.type = "button";
      confirm.addEventListener("click", async () => {
        confirm.disabled = true;
        try {
          await api("/api/recycle-file", {id:file.id, version:file.version});
          pendingRecycleId = ""; lastFiles = ""; showError(""); await poll();
        } catch (error) {
          confirm.disabled = false; showError(error.message);
        }
      });
      const cancel = element("button", "", "Cancel");
      cancel.type = "button";
      cancel.addEventListener("click", () => { pendingRecycleId = ""; lastFiles = ""; renderFiles(overview); });
      actions.append(confirm, cancel);
    } else {
      const recycle = element("button", "recycle-action", "Recycle");
      recycle.type = "button";
      recycle.setAttribute("aria-label", `Recycle ${file.name}`);
      recycle.addEventListener("click", () => { pendingRecycleId = file.id; lastFiles = ""; renderFiles(overview); });
      actions.append(recycle);
    }
    row.append(label, actions); reports.append(row);
  }
  const apps = $("appsList"); clear(apps);
  const saved = Array.isArray(overview.apps) ? overview.apps : [];
  if (!saved.length) apps.append(element("p", "quiet", "No saved app bundles."));
  for (const app of saved) {
    const row = element("article", "file-item");
    const label = element("div", "");
    label.append(element("strong", "", app.name));
    label.append(element("p", "", `Saved bundle · ${app.slug}`));
    row.append(label); apps.append(row);
  }
}

async function poll() {
  if (polling) return;
  polling = true;
  try {
    const data = await api("/api/snapshot");
    renderHealth(data.health || {});
    renderEvents(Array.isArray(data.events) ? data.events : []);
    lastOverview = data.overview || {};
    if (currentView === "activity") renderActivity(lastOverview);
    if (currentView === "abilities") renderAbilities(lastOverview.capabilities || []);
    if (currentView === "files") renderFiles(lastOverview);
    setText("androidStatus", lastOverview.android || "Android status unavailable.");
  } catch (error) {
    renderHealth({brain:false, visualizer:false});
    setText("connectionText", "Cockpit unavailable");
  } finally { polling = false; }
}

document.querySelectorAll(".view-tab").forEach((tab) => tab.addEventListener("click", () => switchView(tab.dataset.view)));
$("abilitySearch").addEventListener("input", () => renderAbilities((lastOverview || {}).capabilities || []));
$("spatialView").addEventListener("click", () => switchView("spatial"));
$("refreshMics").addEventListener("click", refreshMics);
$("refreshCameras").addEventListener("click", refreshCameras);
$("saveMic").addEventListener("click", async () => {
  $("saveMic").disabled = true;
  try {
    await api("/api/select-mic", {device: $("micSelect").value});
    setText("micFeedback", "Saved. Hold HOME for the next capture to test it.");
  } catch (error) { setText("micFeedback", error.message); }
  finally { $("saveMic").disabled = false; }
});
$("useCamera").addEventListener("click", () => {
  sessionStorage.setItem("jarvis-draft", $("prompt").value);
  const next = new URL(location.href);
  const id = $("cameraSelect").value;
  if (id) next.searchParams.set("spatialCam", id);
  else next.searchParams.delete("spatialCam");
  next.searchParams.set("spatialCamera", "1");
  next.searchParams.set("spatialView", "1");
  location.assign(next.href);
});
$("spatialCamera").addEventListener("click", () => {
  sessionStorage.setItem("jarvis-draft", $("prompt").value);
  const next = new URL(location.href);
  if (next.searchParams.get("spatialCamera") === "1") next.searchParams.delete("spatialCamera");
  else next.searchParams.set("spatialCamera", "1");
  next.searchParams.set("spatialView", "1");
  location.assign(next.href);
});
$("prepareAndroid").addEventListener("click", () => {
  $("prompt").value = "Check my Android phone connection and report what is actually available.";
  $("prompt").focus();
});
$("preparePresentation").addEventListener("click", () => {
  $("prompt").value = "Create a professional, source-linked PowerPoint presentation about ";
  $("prompt").focus();
});
$("prompt").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault(); $("composer").requestSubmit();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.ctrlKey && !event.altKey && !event.shiftKey && event.key.toLowerCase() === "l") {
    event.preventDefault(); $("prompt").focus();
  }
});
$("composer").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const text = $("prompt").value.trim();
  if (!text) return;
  busy = true; $("sendButton").disabled = true; showError("");
  try {
    await api("/api/send", {text});
    $("prompt").value = "";
    await poll();
  } catch (error) { showError(error.message); }
  finally { busy = false; $("sendButton").disabled = false; $("prompt").focus(); }
});

const draft = sessionStorage.getItem("jarvis-draft");
if (draft !== null) { $("prompt").value = draft; sessionStorage.removeItem("jarvis-draft"); }
switchView(new URLSearchParams(location.search).get("spatialView") === "1" ? "spatial" : "board");
poll();
setInterval(poll, 1500);
