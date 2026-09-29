"""Mount the unmodified Board source as a scoped, iframe-free app component.

The original AGPL Board and core remain the source of the rendering algorithm.
This adapter is deliberately strict about the source revision and substitutions:
an upstream change must be reviewed rather than silently changing the app UI.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


BOARD_SHA256 = "6E0FF638BA86DDBFD249210F77FD0CF2104A5C48810D2DC38B275806CDFE7F02"
CORE_SHA256 = "D6658A0945E59A8D5806E9A83CBAF90E0096DE007BF998EA034C8A40D0AA4115"
BOARD_TAG = '<script src="../../core.js"></script>'


def _replace_once(value: str, before: str, after: str) -> str:
    count = value.count(before)
    if count != 1:
        raise ValueError(f"Board adapter expected one {before!r}, found {count}")
    return value.replace(before, after, 1)


class DirectBoard:
    def __init__(self, root: Path):
        base = Path(root).resolve() / "components" / "ai-visualizer"
        board = (base / "faces" / "board" / "index.html").read_bytes()
        core = (base / "core.js").read_bytes()
        if hashlib.sha256(board).hexdigest().upper() != BOARD_SHA256:
            raise ValueError("Board source changed; review direct-app adapter before running")
        if hashlib.sha256(core).hexdigest().upper() != CORE_SHA256:
            raise ValueError("Visualizer core changed; review direct-app adapter before running")
        core_text = core.decode("utf-8").replace("\r\n", "\n")
        core_text = _replace_once(
            core_text, "position:fixed;left:64px;bottom:14px",
            "position:absolute;left:64px;bottom:14px")
        core_text = _replace_once(
            core_text, 'addEventListener("mousemove", () => {',
            'document.getElementById("boardMount").addEventListener("mousemove", () => {')
        core_text = _replace_once(
            core_text, "document.body.appendChild(sndBtn);",
            'document.getElementById("boardMount").appendChild(sndBtn);')
        self.core_js = core_text.encode("utf-8")
        self.thinking_wav = (base / "assets" / "thinking.wav").read_bytes()
        self.css, self.js = self._adapt(board.decode("utf-8").replace("\r\n", "\n"))

    @staticmethod
    def _adapt(source: str) -> tuple[bytes, bytes]:
        if source.count(BOARD_TAG) != 1 or source.count("<style>") != 1:
            raise ValueError("Board document structure changed")
        style = source.split("<style>", 1)[1].split("</style>", 1)[0]
        markup = source.split("<body>", 1)[1].split(BOARD_TAG, 1)[0].strip()
        script = source.split(BOARD_TAG, 1)[1].split("<script>", 1)[1].split("</script>", 1)[0]
        if "<script" in markup or "</body>" in markup:
            raise ValueError("Board markup is no longer an inert fragment")

        style = _replace_once(style, ":root{", ":host{")
        style = _replace_once(style, "html,body{", ":host{position:relative;display:block;")
        style = _replace_once(style, "body{font-family:", ":host{font-family:")
        style = _replace_once(style, "canvas#stage{position:fixed;", "canvas#stage{position:absolute;")
        style = _replace_once(style, "width:100vw;height:100vh", "width:100%;height:100%")
        style = _replace_once(style, ".hud{position:fixed;", ".hud{position:absolute;")
        style = _replace_once(style, "body.cine .hud", ":host(.cine) .hud")
        style = _replace_once(style, "#vig{position:fixed;", "#vig{position:absolute;")

        # The original canvas logic is retained. Only document ownership,
        # dimensions, and local keyboard focus change for an app-sized panel.
        script = _replace_once(script, "innerWidth*DPR", "boardHost.clientWidth*DPR")
        script = _replace_once(script, "innerHeight*DPR", "boardHost.clientHeight*DPR")
        script = _replace_once(script, 'innerWidth+"px"', 'boardHost.clientWidth+"px"')
        script = _replace_once(script, 'innerHeight+"px"', 'boardHost.clientHeight+"px"')
        script = _replace_once(script, "position:fixed;bottom:64px", "position:absolute;bottom:64px")
        script = _replace_once(script, "    frame(dt);\n    if(fpsEl", "    if(boardHost.getClientRects().length) frame(dt); else AV.tick(dt);\n    if(fpsEl")

        prelude = """/* AGPL-3.0-or-later; original Board rendering by Jared Rhodenizer. */
(() => {
  "use strict";
  const boardHost = window.document.getElementById("boardMount");
  if (!boardHost) return;
  const outerDocument = window.document;
  const shadow = boardHost.attachShadow({mode: "open"});
  const sheet = outerDocument.createElement("link");
  sheet.rel = "stylesheet";
  sheet.href = "/assets/board-direct.css";
  shadow.append(sheet);
  const template = outerDocument.createElement("template");
  template.innerHTML = __BOARD_MARKUP__;
  shadow.append(template.content.cloneNode(true));
  const document = {
    getElementById: (id) => shadow.getElementById(id),
    querySelector: (selector) => shadow.querySelector(selector),
    createElement: (tag) => outerDocument.createElement(tag),
    body: boardHost,
    documentElement: boardHost,
    get fullscreenElement() { return outerDocument.fullscreenElement; },
    exitFullscreen: () => outerDocument.exitFullscreen(),
    set title(_value) { /* keep the desktop cockpit window title */ }
  };
  const addEventListener = (name, handler) => boardHost.addEventListener(name, handler);
  boardHost.addEventListener("pointerdown", () => boardHost.focus());
""".replace("__BOARD_MARKUP__", json.dumps(markup, ensure_ascii=False))
        postlude = """
  new ResizeObserver(() => {
    if (boardHost.clientWidth && boardHost.clientHeight) resize();
  }).observe(boardHost);
})();
"""
        return style.encode("utf-8"), (prelude + script + postlude).encode("utf-8")
