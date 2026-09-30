"""Native WebView2 cockpit with original Board and Spatial renderers mounted directly.

Both adapters pin the original sources. Camera-free Spatial preview is
available; camera/gesture parity still requires a physical camera. This shell
uses the same Backtalk session as voice and exposes only a scoped localhost API.
"""

from __future__ import annotations

import hmac
import html
import base64
import hashlib
import json
import os
import re
import secrets
import threading
import urllib.parse
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from client import JarvisClient
from observability import Observability
from created_files import CreatedFileError, recycle_created_file, resolve_created_file
from board_direct import DirectBoard
from spatial_direct import DirectSpatial


ROOT = Path(__file__).resolve().parent.parent
WEB = Path(__file__).resolve().parent / "web"
IMPORT_MAP = json.dumps({"imports": {
    "three": "/vendor/three/build/three.module.js",
    "three/addons/": "/vendor/three/examples/jsm/",
}}, separators=(",", ":"))
IMPORT_MAP_HASH = base64.b64encode(hashlib.sha256(IMPORT_MAP.encode()).digest()).decode()
VENDOR_HASHES = {
    "/vendor/three/build/three.module.js": "76DEA8151BC9352AEF3528B4262E249B2604F62543828328DB978D060D61A495",
    "/vendor/three/examples/jsm/loaders/GLTFLoader.js": "D073B438E6A07E1359741DD5D6C76C953420CC0D4FD84EB1BDDE94315540E6A3",
    "/vendor/three/examples/jsm/environments/RoomEnvironment.js": "E21F41B7EF2016F2984A5D27850B42DFFA797A6A194A138E288B06576D765A7B",
    "/vendor/three/examples/jsm/utils/BufferGeometryUtils.js": "9BE041E96308775D00E2695CC607645B9A9B64FD7C0E759DD8F7C00A8D92BECB",
    "/vendor/vision/vision_bundle.mjs": "E77F281F9619150D937023C355BAE170E9120E3B9E43F1E23A2A7BEE07197669",
    "/vendor/vision/wasm/vision_wasm_internal.js": "9440CF0CC0CEA21800E31581EC32AEEDCC5FBF9DF4509796BBC7D3F99E52AB9C",
    "/vendor/vision/wasm/vision_wasm_internal.wasm": "F82A8E6C05E08A44CC9F9E7EC5F845935BCBB1B1500EBE8C2F4812FB4E2917DC",
    "/vendor/vision/wasm/vision_wasm_nosimd_internal.js": "ABE9B6FBEAF86FCB53A5EDCE3926C82CCB0619E18FED4D9D9CE561EE7F55E054",
    "/vendor/vision/wasm/vision_wasm_nosimd_internal.wasm": "38B61FEAB2FD7934E05CBE9F68BAA308978A5E3B7F85C1913BB8AE89B8EF8B97",
    "/vendor/model/hand_landmarker.task": "FBC2A30080C3C557093B5DDFC334698132EB341044CCEE322CCF8BCF3607CDE1",
}


def safe_media_path(path: str) -> bool:
    if not path.startswith("/spatial/media/") or len(path) > 4096:
        return False
    relative = path[len("/spatial/media/"):]
    for _ in range(3):
        decoded = urllib.parse.unquote(relative)
        if decoded == relative:
            break
        relative = decoded
    if (not relative or "\\" in relative or "\x00" in relative or
            any(part in {"", ".", ".."} for part in relative.split("/"))):
        return False
    # Media may include glTF sidecars (.bin, textures), but executable
    # documents are never served from the app's privileged origin.
    return Path(relative).suffix.lower() not in {".html", ".htm", ".js", ".mjs", ".svg", ".xml"}


class BoardCockpitServer:
    def __init__(self, root: Path = ROOT, *, board_url: str =
                 "http://127.0.0.1:8790/faces/board/", port: int = 0,
                 client: JarvisClient | None = None,
                 observability: Observability | None = None,
                 direct_board: DirectBoard | None = None,
                 direct_spatial: DirectSpatial | None = None,
                 vendor_root: Path | None = None):
        self.root = Path(root).resolve()
        parsed = urllib.parse.urlparse(board_url)
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
                or not parsed.port or parsed.path != "/faces/board/"
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError("Board URL must be the local face server's /faces/board/ page")
        self.board_url = board_url
        self.board_origin = f"http://127.0.0.1:{parsed.port}"
        self.spatial_url = "http://127.0.0.1:8794/stage.html"
        self.spatial_origin = "http://127.0.0.1:8794"
        self.client = client or JarvisClient(self.root, face_url=self.board_origin)
        self.observability = observability or Observability(self.root)
        self.direct_board = direct_board or DirectBoard(self.root)
        self.direct_spatial = direct_spatial or DirectSpatial(self.root)
        self.vendor_root = Path(vendor_root or self.root / "desktop" / "vendor" / "runtime").resolve()
        for url, expected in VENDOR_HASHES.items():
            file = self.vendor_root / url[len("/vendor/"):]
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest().upper() != expected:
                raise ValueError(f"Pinned desktop vendor asset missing or changed: {url}")
        self.token = secrets.token_urlsafe(32)
        self.server = None
        self.thread = None
        self.port = port

    def start(self) -> str:
        cockpit = self

        class Handler(BaseHTTPRequestHandler):
            def _headers(self, code: int, ctype: str, length: int,
                         extra: tuple[tuple[str, str], ...] = ()) -> None:
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(length))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("X-Frame-Options", "DENY")
                for name, value in extra:
                    self.send_header(name, value)
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'none'; "
                    f"script-src 'self' 'sha256-{IMPORT_MAP_HASH}' 'wasm-unsafe-eval'; "
                    "style-src 'self'; "
                    "connect-src 'self'; worker-src 'self' blob:; "
                    "img-src 'self' data: blob:; media-src 'self' blob:; font-src 'self'; "
                    "base-uri 'none'; form-action 'none'")
                self.end_headers()

            def _send(self, code: int, body: bytes, ctype: str) -> None:
                try:
                    self._headers(code, ctype, len(body))
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                    # A WebView closing during the 120 ms signal poll is a
                    # normal disconnect, not a visualizer/service failure.
                    pass

            def _json(self, code: int, payload: dict) -> None:
                self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                           "application/json; charset=utf-8")

            def _authorized(self) -> bool:
                return hmac.compare_digest(
                    self.headers.get("X-Jarvis-Session", ""), cockpit.token)

            def _origin_ok(self) -> bool:
                origin = self.headers.get("Origin")
                return not origin or origin == f"http://127.0.0.1:{cockpit.port}"

            def do_GET(self) -> None:
                path = urllib.parse.urlsplit(self.path).path
                if path == "/session/" + cockpit.token:
                    template = (WEB / "index.html").read_text(encoding="utf-8")
                    body = (template.replace("__JARVIS_SESSION_TOKEN__",
                                             html.escape(cockpit.token, quote=True))
                            .replace("__JARVIS_BOARD_URL__",
                                     html.escape(cockpit.board_url, quote=True))
                            .replace("__JARVIS_SPATIAL_URL__",
                                     html.escape(cockpit.spatial_url, quote=True))
                            .replace("__JARVIS_IMPORT_MAP__", IMPORT_MAP)).encode("utf-8")
                    self._send(200, body, "text/html; charset=utf-8")
                    return
                if path == "/assets/app.css":
                    self._send(200, (WEB / "app.css").read_bytes(), "text/css; charset=utf-8")
                    return
                if path == "/assets/files.css":
                    self._send(200, (WEB / "files.css").read_bytes(), "text/css; charset=utf-8")
                    return
                if path == "/assets/devices.css":
                    self._send(200, (WEB / "devices.css").read_bytes(), "text/css; charset=utf-8")
                    return
                if path == "/assets/spatial.css":
                    self._send(200, (WEB / "spatial.css").read_bytes(), "text/css; charset=utf-8")
                    return
                if path == "/assets/app.js":
                    self._send(200, (WEB / "app.js").read_bytes(),
                               "text/javascript; charset=utf-8")
                    return
                if path == "/assets/board-core.js":
                    self._send(200, cockpit.direct_board.core_js,
                               "text/javascript; charset=utf-8")
                    return
                if path == "/assets/board-direct.js":
                    self._send(200, cockpit.direct_board.js,
                               "text/javascript; charset=utf-8")
                    return
                if path == "/assets/board-direct.css":
                    self._send(200, cockpit.direct_board.css,
                               "text/css; charset=utf-8")
                    return
                if path == "/assets/spatial-direct.js":
                    self._send(200, cockpit.direct_spatial.js,
                               "text/javascript; charset=utf-8")
                    return
                if path == "/assets/spatial-direct.css":
                    self._send(200, cockpit.direct_spatial.css,
                               "text/css; charset=utf-8")
                    return
                if path == "/assets/assets/thinking.wav":
                    self._send(200, cockpit.direct_board.thinking_wav,
                               "audio/wav")
                    return
                if path in VENDOR_HASHES:
                    file = cockpit.vendor_root / path[len("/vendor/"):]
                    ctype = ("application/wasm" if path.endswith(".wasm") else
                             "text/javascript; charset=utf-8" if path.endswith((".js", ".mjs")) else
                             "application/octet-stream")
                    self._send(200, file.read_bytes(), ctype)
                    return
                if path in {"/spatial/config", "/spatial/tree", "/spatial/props",
                            "/spatial/note", "/spatial/orb", "/spatial/state"} or path.startswith("/spatial/media/"):
                    if len(self.path) > 8192 or (path.startswith("/spatial/media/") and
                                                  not safe_media_path(path)):
                        self._json(400, {"error": "invalid spatial path"})
                        return
                    try:
                        target = cockpit.spatial_origin + self.path[len("/spatial"):]
                        headers = {}
                        is_media = path.startswith("/spatial/media/")
                        range_header = self.headers.get("Range", "")
                        if is_media and re.fullmatch(r"bytes=\d*-\d*", range_header):
                            headers["Range"] = range_header
                        request = urllib.request.Request(target, headers=headers)
                        with urllib.request.urlopen(request, timeout=5) as response:
                            redirected = urllib.parse.urlsplit(response.geturl())
                            if (redirected.scheme != "http" or
                                    redirected.netloc != urllib.parse.urlsplit(cockpit.spatial_origin).netloc):
                                raise ValueError("unexpected spatial redirect")
                            ctype = response.headers.get("Content-Type", "application/octet-stream")
                            if is_media:
                                length = int(response.headers.get("Content-Length", "-1"))
                                if not 0 <= length <= 4 * 1024 * 1024 * 1024:
                                    self._json(413, {"error": "spatial asset size unavailable or too large"})
                                    return
                                extra = []
                                content_range = response.headers.get("Content-Range", "")
                                if response.status == 206 and re.fullmatch(r"bytes \d+-\d+/\d+", content_range):
                                    extra.append(("Content-Range", content_range))
                                    extra.append(("Accept-Ranges", "bytes"))
                                self._headers(response.status, ctype, length, tuple(extra))
                                remaining = length
                                while remaining:
                                    chunk = response.read(min(65536, remaining))
                                    if not chunk:
                                        break
                                    self.wfile.write(chunk)
                                    remaining -= len(chunk)
                            else:
                                data = response.read(8 * 1024 * 1024 + 1)
                                if len(data) > 8 * 1024 * 1024:
                                    self._json(413, {"error": "spatial response too large"})
                                    return
                                self._send(200, data, ctype)
                    except urllib.error.HTTPError as error:
                        self._json(error.code if error.code in {404, 416} else 503,
                                   {"error": "spatial resource unavailable"})
                    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                        pass
                    except (OSError, ValueError):
                        self._json(503, {"error": "spatial service unavailable"})
                    return
                if path in {"/state", "/config"}:
                    try:
                        request = urllib.request.Request(
                            cockpit.board_origin + path,
                            headers={"Cache-Control": "no-store"})
                        with urllib.request.urlopen(request, timeout=0.8) as response:
                            payload = json.loads(response.read(128_001))
                        if not isinstance(payload, dict):
                            raise ValueError("invalid visualizer reply")
                        if path == "/config":
                            payload = {key: payload[key] for key in
                                       ("name", "badge", "thinking_sound")
                                       if key in payload}
                        self._json(200, payload)
                    except (OSError, ValueError, TypeError):
                        self._json(503, {"error": "visualizer unavailable"})
                    return
                if path == "/api/snapshot":
                    if not self._authorized():
                        self._json(403, {"error": "unauthorized"})
                        return
                    try:
                        health = cockpit.client.health()
                        events = cockpit.client.events() if health["brain"] else []
                        overview = cockpit.observability.snapshot()
                    except Exception:
                        self._json(503, {"error": "local status unavailable"})
                        return
                    self._json(200, {"health": health, "events": events,
                                     "overview": overview})
                    return
                if path == "/api/devices":
                    if not self._authorized():
                        self._json(403, {"error": "unauthorized"})
                        return
                    try:
                        self._json(200, cockpit.client.devices())
                    except Exception:
                        self._json(503, {"error": "audio device service unavailable"})
                    return
                self._json(404, {"error": "not found"})

            def do_POST(self) -> None:
                if not self._authorized() or not self._origin_ok():
                    self._json(403, {"error": "unauthorized"})
                    return
                path = urllib.parse.urlsplit(self.path).path
                if path == "/spatial/state":
                    try:
                        size = int(self.headers.get("Content-Length", "0"))
                        if not 0 < size <= 262144:
                            raise ValueError("invalid spatial state length")
                        body = self.rfile.read(size)
                        request = urllib.request.Request(cockpit.spatial_origin + "/state",
                                                         data=body, method="POST")
                        with urllib.request.urlopen(request, timeout=1.5) as response:
                            commands = response.read(262145)
                        if len(commands) > 262144:
                            raise ValueError("spatial command response too large")
                        self._send(200, commands, "application/json; charset=utf-8")
                    except (OSError, ValueError):
                        self._json(503, {"error": "spatial service unavailable"})
                    return
                if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
                    self._json(415, {"error": "application/json required"})
                    return
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size <= 16384:
                        raise ValueError("invalid size")
                    payload = json.loads(self.rfile.read(size))
                    if not isinstance(payload, dict):
                        raise ValueError("invalid body")
                except (ValueError, TypeError):
                    self._json(400, {"error": "invalid request"})
                    return
                if path == "/api/send":
                    try:
                        cockpit.client.send(payload.get("text", ""))
                    except ValueError:
                        self._json(400, {"error": "message must be 1-4000 characters"})
                    except Exception:
                        self._json(503, {"error": "agent did not accept the message"})
                    else:
                        self._json(202, {"accepted": True})
                    return
                if path == "/api/select-mic":
                    name = payload.get("device")
                    if not isinstance(name, str) or len(name) > 300:
                        self._json(400, {"error": "invalid microphone"})
                        return
                    try:
                        self._json(200, cockpit.client.select_microphone(name))
                    except urllib.error.HTTPError as exc:
                        self._json(exc.code if exc.code in {400, 409} else 503,
                                   {"error": "microphone no longer available or setting failed"})
                    except Exception:
                        self._json(503, {"error": "audio device service unavailable"})
                    return
                if path == "/api/open-report":
                    file_id = payload.get("id")
                    if not isinstance(file_id, str):
                        self._json(400, {"error": "created-file ID required"})
                        return
                    try:
                        target = resolve_created_file(cockpit.root, file_id,
                                                      str(payload.get("version") or ""))
                    except CreatedFileError as exc:
                        self._json(404, {"error": str(exc)})
                        return
                    except OSError:
                        self._json(404, {"error": "created file is no longer available"})
                        return
                    try:
                        os.startfile(target)
                    except OSError:
                        self._json(503, {"error": "Windows could not open this file; check for an associated PDF or PPTX app"})
                    else:
                        self._json(202, {"requested": True})
                    return
                if path == "/api/recycle-file":
                    try:
                        result = recycle_created_file(cockpit.root, payload.get("id"), payload.get("version"))
                    except CreatedFileError as exc:
                        self._json(409, {"error": str(exc)})
                    else:
                        self._json(200, result)
                    return
                self._json(404, {"error": "not found"})

            def log_message(self, *_args) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       name="jarvis-board-cockpit", daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{self.port}/session/{self.token}"

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            if self.thread is not None:
                self.thread.join(timeout=2)


def main() -> None:
    server = BoardCockpitServer()
    url = server.start()
    try:
        import webview

        webview.create_window("JARVIS — Board cockpit", url,
                              width=1440, height=860, min_size=(980, 640),
                              background_color="#020705", text_select=True)
        # Force the modern installed WebView2 renderer; never silently fall
        # back to the legacy MSHTML engine that cannot render this Board.
        webview.start(gui="edgechromium", private_mode=True)
    finally:
        server.stop()


if __name__ == "__main__":
    main()
