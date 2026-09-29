"""Read-only, privacy-minimized cockpit views of JARVIS-owned state.

No model session or tool runtime is constructed here. In particular, this
module never interprets audit arguments/results as commands or displays them.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))
from created_files import list_created_files


TOOL = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
VERSION = re.compile(r"\d{8}T\d{12}Z\Z")
STATUS = {"verified", "observed", "delivered", "failed", "denied", "unknown"}
DOCUMENT_SUFFIXES = {".pdf", ".docx", ".pptx"}


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _clean_text(value: Any, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def _dict_value(node: ast.AST, key: str) -> ast.AST | None:
    if not isinstance(node, ast.Dict):
        return None
    for source, value in zip(node.keys, node.values):
        if isinstance(source, ast.Constant) and source.value == key:
            return value
    return None


def _constant_string(node: ast.AST | None) -> str:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else ""


class Observability:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.state = self.root / ".jarvis"
        self._capabilities_mtime = None
        self._capabilities_cache: list[dict] = []

    def capabilities(self) -> list[dict]:
        """Read the literal registry without importing or executing agent code."""
        path = self.root / "core" / "jarvis_mark2.py"
        if path.is_symlink() or not path.is_file() or not _within(path, self.root):
            return []
        try:
            mtime = path.stat().st_mtime_ns
            if self._capabilities_mtime == mtime:
                return self._capabilities_cache
            tree = ast.parse(path.read_text(encoding="utf-8"))
            lists = []
            read_only = set()
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    names = [target.id for target in node.targets if isinstance(target, ast.Name)]
                    if "MARK2_TOOLS" in names:
                        if isinstance(node.value, ast.List):
                            lists.append(node.value)
                    if "READ_ONLY_MARK2_TOOLS" in names:
                        read_only = set(ast.literal_eval(node.value))
                elif (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                      and isinstance(node.value.func, ast.Attribute)
                      and isinstance(node.value.func.value, ast.Name)
                      and node.value.func.value.id == "MARK2_TOOLS"
                      and node.value.func.attr == "extend" and len(node.value.args) == 1):
                    if isinstance(node.value.args[0], ast.List):
                        lists.append(node.value.args[0])
            capabilities = []
            seen = set()
            for group in lists:
                for item in group.elts:
                    function = _dict_value(item, "function")
                    name = _constant_string(_dict_value(function, "name"))
                    if not name or not TOOL.fullmatch(name) or name in seen:
                        continue
                    seen.add(name)
                    capabilities.append({
                        "name": name,
                        "description": _clean_text(
                            _constant_string(_dict_value(function, "description")), 240),
                        "read_only": name in read_only,
                    })
            self._capabilities_mtime = mtime
            self._capabilities_cache = capabilities
            return capabilities
        except (OSError, SyntaxError, ValueError, TypeError, AttributeError):
            return []

    def audit(self, limit: int = 35) -> list[dict]:
        path = self.state / "audit.jsonl"
        if not path.is_file() or path.is_symlink() or not _within(path, self.root):
            return []
        try:
            with path.open("rb") as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                handle.seek(max(0, size - 256_000))
                raw = handle.read(256_000)
            lines = raw.decode("utf-8", errors="replace").splitlines()
            if size > 256_000 and lines:
                lines = lines[1:]  # first line may be a partial JSON object
        except OSError:
            return []
        records = []
        for line in lines[-max(1, min(limit * 3, 120)):]:
            try:
                event = json.loads(line)
                tool = event.get("tool")
                verification = event.get("verification") or {}
                status = verification.get("status")
                if not isinstance(tool, str) or not TOOL.fullmatch(tool):
                    continue
                if status not in STATUS:
                    status = "unknown"
                timestamp = str(event.get("timestamp") or "")[:40]
                # Deliberately omit args, result, and evidence arrays: older
                # logs or new tools may contain sensitive content there.
                records.append({"tool": tool, "status": status,
                                "timestamp": timestamp,
                                "goal_verified": bool(verification.get("goal_verified"))})
            except (ValueError, TypeError, AttributeError):
                continue
        return records[-max(1, min(limit, 80)):]

    def task(self) -> dict | None:
        folder = self.state / "tasks"
        if not folder.is_dir() or folder.is_symlink() or not _within(folder, self.root):
            return None
        try:
            candidates = sorted(
                (p for p in folder.glob("*.json") if p.is_file() and not p.is_symlink()
                 and _within(p, folder)),
                key=lambda p: p.stat().st_mtime, reverse=True)[:10]
        except OSError:
            return None
        for path in candidates:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or data.get("id") != path.stem:
                    continue
                if data.get("status") not in {"active", "paused", "completed", "cancelled"}:
                    continue
                steps = data.get("steps")
                if not isinstance(steps, list):
                    continue
                clean_steps = []
                for item in steps[:8]:
                    if not isinstance(item, dict):
                        continue
                    clean_steps.append({
                        "id": item.get("id") if isinstance(item.get("id"), int) else 0,
                        "description": _clean_text(item.get("description")),
                        "status": item.get("status") if item.get("status") in {
                            "pending", "verified", "observed"} else "unknown",
                        "kind": item.get("kind") if item.get("kind") in {
                            "act", "observe"} else "unknown",
                    })
                return {"status": data["status"], "steps": clean_steps}
            except (OSError, ValueError, TypeError):
                continue
        return None

    def files(self, limit: int = 40) -> list[dict]:
        return list_created_files(self.root, limit)

    def apps(self, limit: int = 20) -> list[dict]:
        folder = self.state / "generated_apps"
        if not folder.is_dir() or folder.is_symlink() or not _within(folder, self.root):
            return []
        apps = []
        try:
            roots = sorted(folder.iterdir())
        except OSError:
            return []
        for app in roots:
            if len(apps) >= max(1, min(limit, 50)):
                break
            if app.is_symlink() or not app.is_dir() or not re.fullmatch(r"[a-z0-9-]{2,60}", app.name):
                continue
            try:
                pointer = app / "CURRENT"
                if pointer.is_symlink() or not _within(pointer, folder):
                    continue
                version = pointer.read_text(encoding="utf-8").strip()
                if not VERSION.fullmatch(version):
                    continue
                manifest_path = app / "versions" / version / "manifest.json"
                if manifest_path.is_symlink() or not _within(manifest_path, folder):
                    continue
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest.get("slug") != app.name or manifest.get("version") != version:
                    continue
                apps.append({"name": _clean_text(manifest.get("name") or app.name, 80),
                             "slug": app.name, "version": version})
            except (OSError, ValueError, TypeError, AttributeError):
                continue
        return apps

    @staticmethod
    def android_readiness() -> str:
        configured = os.environ.get("JARVIS_ADB_PATH", "").strip()
        adb = Path(configured).is_file() if configured else bool(shutil.which("adb"))
        if not adb:
            local = os.environ.get("LOCALAPPDATA", "")
            adb = bool(local and (Path(local) / "Android" / "Sdk" /
                                  "platform-tools" / "adb.exe").is_file())
        if not adb:
            return "Platform-Tools not found. Phone control is unavailable."
        if not os.environ.get("JARVIS_ANDROID_SERIAL", "").strip():
            return "Platform-Tools found. No exact phone serial configured."
        return "Phone serial configured. Connection is not verified in this view."

    def snapshot(self) -> dict:
        return {"audit": self.audit(), "task": self.task(),
                "files": self.files(), "apps": self.apps(),
                "android": self.android_readiness(),
                "capabilities": self.capabilities()}


def local_time(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%H:%M:%S")
    except ValueError:
        return "--:--:--"
