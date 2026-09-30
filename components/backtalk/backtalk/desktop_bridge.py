"""Loopback-only desktop client bridge for the existing voice session.

This deliberately does not create another agent or microphone owner. The
desktop client's typed turns enter Backtalk's existing typed queue.
"""

from __future__ import annotations

import hmac
import json
import os
import secrets
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Queue


class DesktopBridge:
    def __init__(self, typed_queue: Queue, signals_dir: str | Path, port: int = 8792,
                 list_mics=None, select_mic=None):
        self.typed_queue = typed_queue
        self.token_path = Path(signals_dir) / ".desktop_bridge_token"
        self.port = port
        self.list_mics = list_mics
        self.select_mic = select_mic
        self.token = secrets.token_urlsafe(32)
        self.events = deque(maxlen=80)
        self.sequence = 0
        self.lock = threading.Lock()
        self.server = None
        self.thread = None

    def publish(self, kind: str, text: str) -> None:
        if kind not in {"user", "assistant", "error"}:
            return
        with self.lock:
            self.sequence += 1
            self.events.append({"id": self.sequence, "kind": kind,
                                "text": str(text)[:10000], "ts": time.time()})

    def start(self) -> None:
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, code: int, payload: dict) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _authorized(self) -> bool:
                # Reject browser-origin requests even if another local page
                # somehow learned the token. Native urllib sends no Origin.
                if self.headers.get("Origin"):
                    return False
                return hmac.compare_digest(
                    self.headers.get("X-Jarvis-Token", ""), bridge.token)

            def do_GET(self) -> None:
                if self.path == "/health":
                    self._send(200, {"service": "jarvis-desktop-bridge", "ready": True})
                    return
                if not self._authorized():
                    self._send(403, {"error": "unauthorized"})
                    return
                if self.path == "/devices":
                    try:
                        self._send(200, bridge.list_mics() if bridge.list_mics else
                                   {"selected": "", "inputs": []})
                    except Exception:
                        self._send(503, {"error": "audio devices unavailable"})
                    return
                if self.path != "/events":
                    self._send(404, {"error": "not found"})
                    return
                with bridge.lock:
                    events = list(bridge.events)
                    sequence = bridge.sequence
                self._send(200, {"sequence": sequence, "events": events})

            def do_POST(self) -> None:
                if not self._authorized():
                    self._send(403, {"error": "unauthorized"})
                    return
                if self.path not in {"/turn", "/mic"}:
                    self._send(404, {"error": "not found"})
                    return
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    size = 0
                if not 0 < size <= 16384:
                    self._send(413, {"error": "invalid request size"})
                    return
                try:
                    payload = json.loads(self.rfile.read(size))
                    if self.path == "/mic":
                        selected = payload["device"]
                        if not isinstance(selected, str) or len(selected) > 300:
                            raise ValueError("invalid mic")
                        try:
                            available = bridge.list_mics() if bridge.list_mics else {"inputs": []}
                        except Exception:
                            self._send(503, {"error": "audio devices unavailable"})
                            return
                        if selected and selected not in {d["id"] for d in available["inputs"]}:
                            self._send(409, {"error": "microphone disconnected; refresh devices"})
                            return
                        if not bridge.select_mic or not bridge.select_mic(selected):
                            self._send(503, {"error": "microphone setting could not be saved"})
                            return
                        self._send(200, {"selected": selected})
                        return
                    message = payload["text"]
                    if not isinstance(message, str):
                        raise ValueError("text must be a string")
                    message = message.strip()
                except (ValueError, KeyError, TypeError):
                    self._send(400, {"error": "invalid request"})
                    return
                if not message or len(message) > 4000:
                    self._send(400, {"error": "text must be 1–4000 characters"})
                    return
                if bridge.typed_queue.qsize() >= 3:
                    self._send(429, {"error": "turn queue is full"})
                    return
                bridge.typed_queue.put(message)
                self._send(202, {"accepted": True})

            def log_message(self, *_args) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.token_path.with_name(self.token_path.name + ".tmp")
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(self.token)
            os.replace(temporary, self.token_path)
        except Exception:
            self.server.server_close()
            raise
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       name="jarvis-desktop-bridge", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            if self.thread is not None:
                self.thread.join(timeout=2)
        try:
            if self.token_path.read_text(encoding="utf-8") == self.token:
                self.token_path.unlink()
        except OSError:
            pass
