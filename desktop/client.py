"""Small, testable localhost client for the JARVIS desktop shell."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class JarvisClient:
    def __init__(self, root: Path, *, bridge_url="http://127.0.0.1:8792",
                 face_url="http://127.0.0.1:8790",
                 hands_url="http://127.0.0.1:8794"):
        self.root = Path(root)
        self.token_path = self.root / "runtime" / "signals" / ".desktop_bridge_token"
        self.bridge_url = bridge_url
        self.face_url = face_url
        self.hands_url = hands_url

    @staticmethod
    def _get(url: str, *, headers: dict | None = None) -> dict:
        request = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(request, timeout=1.5) as response:
            return json.load(response)

    def _headers(self) -> dict:
        token = self.token_path.read_text(encoding="utf-8").strip()
        if not token:
            raise RuntimeError("Desktop bridge token is missing")
        return {"X-Jarvis-Token": token}

    def health(self) -> dict:
        result = {"brain": False, "visualizer": False, "hands": False,
                  "state": "offline", "level": 0.0, "samples": []}
        # A missing hand-board must not delay the brain indicator (or the
        # entire cockpit) by serial timeouts on every refresh.
        with ThreadPoolExecutor(max_workers=3) as pool:
            probes = {
                "brain": pool.submit(self._get, self.bridge_url + "/health"),
                "face": pool.submit(self._get, self.face_url + "/state"),
                "hands": pool.submit(self._get, self.hands_url + "/state"),
            }
            for name, future in probes.items():
                try:
                    reply = future.result()
                    if name == "brain":
                        result["brain"] = (reply.get("service") == "jarvis-desktop-bridge"
                                           and reply.get("ready") is True)
                    elif name == "face" and reply.get("state") in {
                            "idle", "listening", "thinking", "speaking"}:
                        result.update({"visualizer": True, "state": reply["state"],
                                       "level": float(reply.get("level", 0)),
                                       "samples": reply.get("samples") or []})
                    elif name == "hands":
                        result["hands"] = True
                except (OSError, ValueError, TypeError, urllib.error.URLError):
                    pass
        return result

    def events(self) -> list[dict]:
        reply = self._get(self.bridge_url + "/events", headers=self._headers())
        return reply.get("events", [])

    def send(self, text: str) -> None:
        message = text.strip()
        if not message or len(message) > 4000:
            raise ValueError("Message must be 1–4000 characters")
        body = json.dumps({"text": message}).encode("utf-8")
        request = urllib.request.Request(
            self.bridge_url + "/turn", data=body,
            headers={**self._headers(), "Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(request, timeout=3) as response:
            if response.status != 202:
                raise RuntimeError(f"JARVIS did not accept the message ({response.status})")
