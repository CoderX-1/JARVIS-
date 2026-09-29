"""Scope the pinned barehands stage in the desktop cockpit without an iframe.

The upstream AGPL implementation remains the rendering/gesture source.  This
adapter only changes document ownership, dimensions, service URLs, and boot
mode.  A source change must be reviewed before the adapter will run.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


STAGE_SHA256 = "E610915B021ADF6F2942EFEF9B3F96A9D28F207A18B630FCA008938FB4D5A82B"


def _once(source: str, before: str, after: str) -> str:
    count = source.count(before)
    if count != 1:
        raise ValueError(f"Spatial adapter expected one {before!r}; found {count}")
    return source.replace(before, after, 1)


class DirectSpatial:
    def __init__(self, root: Path):
        path = Path(root).resolve() / "components" / "barehands" / "stage.html"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest().upper() != STAGE_SHA256:
            raise ValueError("Spatial source changed; review the direct-app adapter")
        self.css, self.js = self._adapt(raw.decode("utf-8").replace("\r\n", "\n"))

    @staticmethod
    def _adapt(source: str) -> tuple[bytes, bytes]:
        if source.count("<style>") != 1 or source.count('<script type="module">') != 1:
            raise ValueError("Spatial document structure changed")
        style = source.split("<style>", 1)[1].split("</style>", 1)[0]
        markup = source.split('<video id="cam"', 1)[1].split('<script type="module">', 1)[0]
        markup = '<video id="cam"' + markup.strip()
        script = source.split('<script type="module">', 1)[1].split("</script>", 1)[0]
        if "<script" in markup or "</body>" in markup:
            raise ValueError("Spatial markup is not an inert fragment")

        style = _once(style, "html, body {", ":host { position:relative; display:block; isolation:isolate;")
        style = _once(style, "#behind { position:fixed;", "#behind { position:absolute;")
        style = re.sub(r"\bbody:not\((\.[\w-]+)\)", r":host(:not(\1))", style)
        style = re.sub(r"\bbody\.([\w-]+)", r":host(.\1)", style)
        # The first-party WebView panel owns layout and keyboard focus.
        script = _once(script,
                       'import { HandLandmarker, FilesetResolver } from\n  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";',
                       "let HandLandmarker, FilesetResolver;")
        script = _once(script, "  await pickInitialCam();\n  const vision =",
                       '  await pickInitialCam();\n  ({ HandLandmarker, FilesetResolver } = await import("/vendor/vision/vision_bundle.mjs"));\n  const vision =')
        script = _once(script,
                       '"https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"',
                       '"/vendor/vision/wasm"')
        script = _once(script,
                       '"https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"',
                       '"/vendor/model/hand_landmarker.task"')
        script = _once(script, 'const Q = new URLSearchParams(location.search);',
                       'const Q = new URLSearchParams(spatialMode === "tracking" ? "" : "?role=preview");')
        script = re.sub(r"\binnerWidth\b", "spatialHost.clientWidth", script)
        script = re.sub(r"\binnerHeight\b", "spatialHost.clientHeight", script)
        script = _once(script, "if (!RING.live) return;",
                       "if (!RING.live || !spatialHost.getClientRects().length) return;")
        script = script.replace("escT(src)", "escT(spatialMedia(src))")
        script = script.replace("escT(it.src)", "escT(spatialMedia(it.src))")
        script = _once(script, "new GLTFLoader().loadAsync(src)",
                       "new GLTFLoader().loadAsync(spatialMedia(src))")
        script = _once(script, 'document.getElementById("boot").remove();\n  await loadTree();',
                       'document.getElementById("boot").remove();\n  spatialHost.dataset.status = "tracking";\n  await loadTree();')
        preview = '''  renderLoop();
} else if (ROLE === "preview") {
  // Camera-free keyboard/mouse operation uses the original stage's ring,
  // tree, physics, media and command channel. It never claims hand gestures.
  document.getElementById("boot").remove();
  document.getElementById("hint").textContent =
    "Click the ring to open folders · click an orb to browse · click a row to open · drag to move · wheel to scroll · R to reset";
  let previewDrag = null, suppressPreviewClick = false;
  const previewItem = (event) => {
    const path = event.composedPath();
    return items.slice().reverse().find(item => path.includes(item.el));
  };
  spatialHost.addEventListener("pointerdown", event => {
    const item = previewItem(event);
    if (!item || event.button !== 0) return;
    previewDrag = {item, x: event.clientX, y: event.clientY,
                   ox: item.x, oy: item.y, moved: false};
    spatialHost.setPointerCapture(event.pointerId);
  });
  spatialHost.addEventListener("pointermove", event => {
    if (!previewDrag) return;
    const dx = event.clientX - previewDrag.x, dy = event.clientY - previewDrag.y;
    if (Math.hypot(dx, dy) > 5) previewDrag.moved = true;
    if (previewDrag.moved) {
      previewDrag.item.x = previewDrag.ox + dx;
      previewDrag.item.y = previewDrag.oy + dy;
    }
  });
  spatialHost.addEventListener("pointerup", () => {
    if (previewDrag?.moved) suppressPreviewClick = true;
    previewDrag = null;
  });
  spatialHost.addEventListener("pointercancel", () => { previewDrag = null; });
  spatialHost.addEventListener("click", event => {
    if (suppressPreviewClick) { suppressPreviewClick = false; return; }
    const item = previewItem(event);
    if (!item) return;
    if (item.type === "widget") ringToggle(item);
    else if (item.type === "orb") openBrowser(item.def.orb, item.x, item.y);
    else if (item.type === "browser") browserTap(item, {x:event.clientX, y:event.clientY});
    else if (item.type === "card" && item.def.file) openPanel(item);
    else if (presented === item) endPresent();
    else if (item.type === "img" || item.type === "model" || item.type === "panel") presentItem(item);
  });
  spatialHost.addEventListener("wheel", event => {
    const item = previewItem(event);
    if (!item || !item.body) return;
    const max = Math.max(0, item.body.offsetHeight - item.body.parentElement.clientHeight + 40);
    item.sTarget = Math.max(0, Math.min(max, (item.sTarget ?? item.scrollY ?? 0) + event.deltaY));
    event.preventDefault();
  }, {passive:false});
  loadTree().then(() => {
    spawnStage(0.5, 0.42);
    spatialHost.dataset.status = "preview";
    let last = performance.now();
    const previewFrame = now => {
      const dt = Math.min((now - last) / 1000, 0.05); last = now;
      physics(dt); renderModels(); renderRings(); pushState(now);
      requestAnimationFrame(previewFrame);
    };
    requestAnimationFrame(previewFrame);
  }).catch(error => {
    spatialHost.dataset.status = "error";
    spatialHost.textContent = "Spatial preview could not start: " + error.message;
  });
} else {
  boot().catch(e => {
    spatialHost.dataset.status = "camera-error";'''
        script = _once(script, '  renderLoop();\n} else {\n  boot().catch(e => {', preview)

        # Three's addon modules contain bare `three` imports.  The import map
        # lives in the main document and is hash-authorized by the CSP.
        prelude = '''/* AGPL-3.0-or-later; original barehands by Jared Rhodenizer. */
const spatialHost = window.document.getElementById("spatialMount");
if (!spatialHost) throw new Error("Spatial mount missing");
const spatialMode = new URLSearchParams(window.location.search).get("spatialCamera") === "1"
  ? "tracking" : "preview";
const outerDocument = window.document;
const spatialShadow = spatialHost.attachShadow({mode: "open"});
const spatialSheet = outerDocument.createElement("link");
spatialSheet.rel = "stylesheet";
spatialSheet.href = "/assets/spatial-direct.css";
spatialShadow.append(spatialSheet);
const spatialTemplate = outerDocument.createElement("template");
spatialTemplate.innerHTML = __MARKUP__;
spatialShadow.append(spatialTemplate.content.cloneNode(true));
spatialHost.dataset.status = "starting";
spatialHost.dataset.mode = spatialMode;
spatialHost.addEventListener("pointerdown", () => spatialHost.focus());
const document = {
  getElementById: (id) => spatialShadow.getElementById(id),
  createElement: (tag) => outerDocument.createElement(tag),
  body: spatialHost,
  documentElement: spatialHost
};
const addEventListener = (name, handler) => spatialHost.addEventListener(name, handler);
const nativeFetch = window.fetch.bind(window);
const fetch = (url, options = {}) => {
  if (typeof url !== "string" || !url.startsWith("/")) return nativeFetch(url, options);
  const headers = new Headers(options.headers || {});
  if (options.method?.toUpperCase() === "POST")
    headers.set("X-Jarvis-Session", outerDocument.querySelector('meta[name="session-token"]').content);
  return nativeFetch("/spatial" + url, {...options, headers});
};
const spatialMedia = (url) => typeof url === "string" && url.startsWith("/media/")
  ? "/spatial" + url : url;
const requestAnimationFrame = (callback) => {
  if (!spatialHost.isConnected) return 0;
  return window.requestAnimationFrame((time) => {
    if (!spatialHost.isConnected) return;
    if (spatialHost.getClientRects().length) callback(time);
    else window.setTimeout(() => requestAnimationFrame(callback), 250);
  });
};
'''.replace("__MARKUP__", json.dumps(markup, ensure_ascii=False))
        return style.encode("utf-8"), (prelude + script).encode("utf-8")
