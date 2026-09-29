"""JARVIS desktop cockpit. Uses the existing voice/agent process."""

from __future__ import annotations

import math
import os
import queue
import sys
import threading
import tkinter as tk
import urllib.error
import webbrowser
from pathlib import Path
from tkinter import font as tkfont

from client import JarvisClient
from observability import Observability, local_time


ROOT = Path(__file__).resolve().parent.parent
NAVY = "#07111C"
PANEL = "#0C1B2A"
STEEL = "#142638"
LINE = "#24465A"
IVORY = "#E9F2F5"
MUTED = "#91A9B5"
CYAN = "#56D7F0"
AMBER = "#F6BD60"
CORAL = "#F47C7C"


class Cockpit(tk.Tk):
    def __init__(self, client: JarvisClient | None = None):
        super().__init__()
        self.client = client or JarvisClient(ROOT)
        self.observability = Observability(self.client.root)
        self.title("JARVIS  /  DESKTOP COMMAND")
        self.configure(bg=NAVY)
        self.geometry("1320x820")
        self.minsize(1030, 650)
        self.fonts = {}
        self.ui_queue = queue.Queue()
        self.last_event = 0
        self.connection = None
        self.overview = None
        self.capabilities_data = []
        self.filtered_caps = []
        self.active_view = "core"
        self.voice_state = "offline"
        self.level = 0.0
        self.samples = []
        self.motion = True
        self.phase = 0.0
        self.polling = False
        self.closed = False
        self._build()
        self.bind("<Control-l>", lambda _e: self.command.focus_set())
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(100, self._drain)
        self.after(100, self._schedule_poll)
        self.after(100, self._animate)

    def _font(self, family="Segoe UI", size=10, weight="normal"):
        key = (family, size, weight)
        if key not in self.fonts:
            self.fonts[key] = tkfont.Font(root=self, family=family,
                                          size=size, weight=weight)
        return self.fonts[key]

    def _label(self, parent, text, *, color=IVORY, size=10, weight="normal",
               family="Segoe UI", **kwargs):
        return tk.Label(parent, text=text, fg=color, bg=parent.cget("bg"),
                        font=self._font(family, size, weight), **kwargs)

    def _build(self):
        top = tk.Frame(self, bg=NAVY, height=92)
        top.pack(fill="x")
        top.pack_propagate(False)
        brand = tk.Frame(top, bg=NAVY)
        brand.pack(side="left", padx=30, pady=12)
        self._label(brand, "JARVIS", size=23, weight="bold").pack(anchor="w")
        self._label(brand, "DESKTOP COMMAND  /  MARK II", color=MUTED,
                    size=9, family="Consolas").pack(anchor="w")
        self.status = self._label(top, "CONNECTING", color=AMBER, size=10,
                                  family="Consolas")
        self.status.pack(side="right", padx=34)
        tk.Frame(self, bg=LINE, height=1).pack(fill="x")

        body = tk.Frame(self, bg=NAVY)
        body.pack(fill="both", expand=True, padx=18, pady=18)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        self.left = tk.Frame(body, bg=PANEL, width=190)
        self.left.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        self.left.pack_propagate(False)
        self.center = tk.Frame(body, bg=PANEL)
        self.center.grid(row=0, column=1, sticky="nsew", padx=(0, 12))
        self.right = tk.Frame(body, bg=PANEL, width=350)
        self.right.grid(row=0, column=2, sticky="ns")
        self.right.pack_propagate(False)
        self._left_panel()
        self._center_panel()
        self._right_panel()

        foot = tk.Frame(self, bg=NAVY, height=38)
        foot.pack(fill="x")
        self._label(foot, "ONE BRAIN  /  VOICE + TEXT + TOOLS", color=MUTED,
                    size=9, family="Consolas").pack(side="left", padx=30)
        self._label(foot, "HOLD HOME TO SPEAK  •  CTRL+L TO TYPE", color=MUTED,
                    size=9, family="Consolas").pack(side="right", padx=30)
        # Reserve the bottom command strip before the flexible center panels.
        body.pack_forget()
        foot.pack_forget()
        foot.pack(side="bottom", fill="x")
        body.pack(fill="both", expand=True, padx=18, pady=18)

    def _left_panel(self):
        self._label(self.left, "System", color=CYAN, size=11,
                    weight="bold").pack(anchor="w", padx=20, pady=(22, 12))
        self.indicators = {}
        for key, title in (
            ("brain", "Agent session"),
            ("visualizer", "Voice signal"),
            ("hands", "Spatial board"),
        ):
            row = tk.Frame(self.left, bg=PANEL)
            row.pack(fill="x", padx=18, pady=5)
            dot = self._label(row, "●", color=MUTED, size=14)
            dot.pack(side="left", anchor="n", padx=(0, 10))
            self._label(row, title, size=10).pack(side="left", anchor="center")
            self.indicators[key] = dot
        tk.Frame(self.left, bg=LINE, height=1).pack(fill="x", padx=18, pady=15)
        self._label(self.left, "Views", color=CYAN, size=11,
                    weight="bold").pack(anchor="w", padx=20, pady=(0, 7))
        self.view_buttons = {}
        for key, title in (("core", "Live core"), ("activity", "Action history"),
                           ("abilities", "Abilities"), ("files", "Created files"),
                           ("devices", "Android")):
            button = tk.Button(
                self.left, text=title, anchor="w", command=lambda k=key: self._set_view(k),
                bg=STEEL if key == "core" else PANEL, fg=IVORY,
                activebackground=LINE, activeforeground=IVORY, bd=0,
                highlightthickness=1, highlightcolor=CYAN,
                highlightbackground=PANEL, cursor="hand2", padx=20, pady=8)
            button.pack(fill="x", padx=8)
            self.view_buttons[key] = button

    def _center_panel(self):
        self.core_view = tk.Frame(self.center, bg=PANEL)
        self.core_view.pack(fill="both", expand=True)
        head = tk.Frame(self.core_view, bg=PANEL)
        head.pack(fill="x", padx=25, pady=(24, 0))
        self._label(head, "NEURAL CORE", color=CYAN, size=10,
                    weight="bold", family="Consolas").pack(side="left")
        self.mode_label = self._label(head, "OFFLINE", color=MUTED, size=10,
                                      family="Consolas")
        self.mode_label.pack(side="right")
        self.canvas = tk.Canvas(self.core_view, bg=PANEL, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=20)
        self.canvas.bind("<Configure>", lambda _e: self._draw_core())
        desc = tk.Frame(self.core_view, bg=PANEL)
        desc.pack(fill="x", padx=28, pady=(0, 30))
        self._label(desc, "A single live session", size=17,
                    weight="bold").pack(anchor="w")
        self._label(desc, "Speak with HOME or type a mission. JARVIS uses the same "
                    "agent, memory and tools from either input.",
                    color=MUTED, size=10, justify="left", wraplength=340).pack(
                        anchor="w", pady=(7, 0))
        workspaces = tk.Frame(desc, bg=PANEL)
        workspaces.pack(anchor="w", pady=(12, 0))
        for title, url in (("Spatial board", "http://127.0.0.1:8794/stage.html"),
                           ("Full visualizer", "http://127.0.0.1:8790/faces/board/")):
            tk.Button(workspaces, text=title,
                      command=lambda u=url: webbrowser.open(u),
                      bg=STEEL, fg=IVORY, activebackground=LINE,
                      activeforeground=IVORY, bd=0, cursor="hand2",
                      padx=10, pady=6).pack(side="left", padx=(0, 8))
        self.motion_button = tk.Button(
            workspaces, text="Motion: on", command=self._toggle_motion,
            bg=STEEL, fg=IVORY, activebackground=LINE, activeforeground=IVORY,
            bd=0, cursor="hand2", padx=10, pady=6)
        self.motion_button.pack(side="left")

        self.activity_view = self._workspace_frame(
            "Action history", "Recent tool outcomes from the agent's local audit."
            " Verified is different from sent or merely observed.")
        self.task_line = self._label(self.activity_view, "No task plan yet.",
                                     color=MUTED, wraplength=340, justify="left")
        self.task_line.pack(anchor="w", fill="x", padx=26, pady=(10, 8))
        self.activity_text = tk.Text(
            self.activity_view, bg=PANEL, fg=IVORY, bd=0, wrap="word",
            state="disabled", padx=26, pady=14,
            font=self._font("Consolas", 10), spacing3=9,
            selectbackground=LINE)
        self.activity_text.pack(fill="both", expand=True)
        for tag, color in (("verified", CYAN), ("observed", MUTED),
                           ("delivered", AMBER), ("unknown", AMBER),
                           ("failed", CORAL), ("denied", CORAL)):
            self.activity_text.tag_configure(tag, foreground=color)

        self.abilities_view = self._workspace_frame(
            "Abilities", "Registered Mark II tools from the installed core."
            " A listed tool may still require an app, provider, permission, or device.")
        search_row = tk.Frame(self.abilities_view, bg=STEEL)
        search_row.pack(fill="x", padx=26, pady=(13, 11))
        self.capability_search = tk.Entry(
            search_row, bg=STEEL, fg=IVORY, insertbackground=CYAN,
            relief="flat", font=self._font("Segoe UI", 10))
        self.capability_search.pack(fill="x", padx=12, pady=9)
        self.capability_search.bind("<KeyRelease>", self._filter_capabilities)
        self.capability_count = self._label(
            self.abilities_view, "Reading installed registry...", color=MUTED)
        self.capability_count.pack(anchor="w", padx=26, pady=(0, 8))
        self.capability_list = tk.Listbox(
            self.abilities_view, bg=PANEL, fg=IVORY,
            selectbackground=STEEL, selectforeground=CYAN,
            highlightthickness=1, highlightbackground=LINE,
            highlightcolor=CYAN, bd=0, activestyle="none",
            font=self._font("Consolas", 10))
        self.capability_list.pack(fill="both", expand=True, padx=26)
        self.capability_list.bind("<<ListboxSelect>>", self._select_capability)
        self.capability_detail = self._label(
            self.abilities_view, "Select a tool to read what it is registered to do.",
            color=MUTED, wraplength=340, justify="left")
        self.capability_detail.pack(anchor="w", fill="x", padx=26, pady=(12, 22))

        self.files_view = self._workspace_frame(
            "Created files", "Reports, presentations, and generated apps saved inside JARVIS."
            " Open a file explicitly; app launch still goes through the agent's integrity check.")
        self.file_list = tk.Listbox(
            self.files_view, bg=STEEL, fg=IVORY, selectbackground=LINE,
            selectforeground=IVORY, highlightthickness=1,
            highlightbackground=LINE, highlightcolor=CYAN, bd=0,
            font=self._font("Segoe UI", 10), activestyle="none")
        self.file_list.pack(fill="both", expand=True, padx=26, pady=(12, 12))
        self.file_items = []
        self.files_rendered = False
        self.file_open = tk.Button(
            self.files_view, text="Open selected file", command=self._open_file,
            bg=STEEL, fg=IVORY, activebackground=LINE,
            activeforeground=IVORY, bd=0, cursor="hand2", padx=12, pady=8)
        self.file_open.pack(anchor="w", padx=26, pady=(0, 16))
        self.apps_line = self._label(self.files_view, "No generated apps yet.",
                                     color=MUTED, wraplength=340, justify="left")
        self.apps_line.pack(anchor="w", fill="x", padx=26, pady=(0, 24))

        self.devices_view = self._workspace_frame(
            "Android", "Device control is gated by an exact serial and live readback."
            " This panel never claims a phone is connected from configuration alone.")
        self.device_line = self._label(self.devices_view, "Checking local setup...",
                                       color=MUTED, wraplength=340, justify="left",
                                       size=13)
        self.device_line.pack(anchor="w", padx=26, pady=(24, 18))
        tk.Button(
            self.devices_view, text="Ask JARVIS to check phone status",
            command=lambda: self._prepare_prompt("Check Android status and tell me what is verified."),
            bg=STEEL, fg=IVORY, activebackground=LINE,
            activeforeground=IVORY, bd=0, cursor="hand2", padx=12, pady=9,
        ).pack(anchor="w", padx=26)

    def _workspace_frame(self, title, description):
        frame = tk.Frame(self.center, bg=PANEL)
        self._label(frame, title, size=19, weight="bold").pack(
            anchor="w", padx=26, pady=(24, 7))
        self._label(frame, description, color=MUTED, wraplength=340,
                    justify="left", size=10).pack(anchor="w", padx=26)
        tk.Frame(frame, bg=LINE, height=1).pack(fill="x", padx=26, pady=(20, 0))
        return frame

    def _set_view(self, name):
        views = {"core": self.core_view, "activity": self.activity_view,
                 "abilities": self.abilities_view,
                 "files": self.files_view, "devices": self.devices_view}
        if name not in views:
            return
        for frame in views.values():
            frame.pack_forget()
        views[name].pack(fill="both", expand=True)
        self.active_view = name
        for key, button in self.view_buttons.items():
            button.configure(bg=STEEL if key == name else PANEL,
                             fg=CYAN if key == name else IVORY)

    def _filter_capabilities(self, _event=None):
        term = self.capability_search.get().strip().casefold()
        self.filtered_caps = [item for item in self.capabilities_data
                              if term in item["name"].casefold()
                              or term in item["description"].casefold()]
        self.capability_list.delete(0, "end")
        for item in self.filtered_caps:
            self.capability_list.insert("end", item["name"].replace("_", " "))
        actions = sum(not item["read_only"] for item in self.capabilities_data)
        self.capability_count.configure(
            text=f"{len(self.filtered_caps)} shown  ·  {len(self.capabilities_data)} registered  ·  {actions} action tools")
        self.capability_detail.configure(
            text="Select a tool to read what it is registered to do.")

    def _select_capability(self, _event=None):
        selection = self.capability_list.curselection()
        if not selection:
            return
        index = int(selection[0])
        if index >= len(self.filtered_caps):
            return
        item = self.filtered_caps[index]
        kind = "Read-only" if item["read_only"] else "Action"
        self.capability_detail.configure(
            text=f"{kind}: {item['description'] or 'No description registered.'}")

    def _prepare_prompt(self, message):
        self.command.delete(0, "end")
        self.command.insert(0, message)
        self.command.focus_set()

    def _open_file(self):
        selection = self.file_list.curselection()
        if not selection:
            self.error_line.configure(text="Select a created file first.")
            return
        index = int(selection[0])
        if index >= len(self.file_items):
            return
        target = Path(self.file_items[index]["path"])
        # Re-check the exact selected path against the bounded JARVIS-owned
        # report shelf; never treat a stale listbox row as file authority.
        if str(target) not in {item["path"] for item in self.observability.files()}:
            self.error_line.configure(text="File changed. Refresh the list before opening it.")
            return
        try:
            os.startfile(target)
            self.error_line.configure(text="")
        except OSError as exc:
            self.error_line.configure(text=f"Could not open file: {type(exc).__name__}. Check its associated app.")

    def _right_panel(self):
        head = tk.Frame(self.right, bg=PANEL)
        head.pack(fill="x", padx=20, pady=(23, 15))
        self._label(head, "CONVERSATION", color=CYAN, size=10,
                    weight="bold", family="Consolas").pack(side="left")
        self._label(head, "LIVE", color=MUTED, size=9,
                    family="Consolas").pack(side="right")
        tk.Frame(self.right, bg=LINE, height=1).pack(fill="x", padx=20)
        self.chat = tk.Text(self.right, bg=PANEL, fg=IVORY, bd=0,
                            wrap="word", state="disabled", padx=20, pady=20,
                            font=self._font("Segoe UI", 10), spacing3=14,
                            insertbackground=CYAN, selectbackground=LINE)
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_configure("author", foreground=CYAN,
                                font=("Consolas", 9, "bold"))
        self.chat.tag_configure("message", foreground=IVORY)
        self.chat.tag_configure("notice", foreground=MUTED)
        self.chat.tag_configure("error", foreground=CORAL)
        self._append("notice", "JARVIS will show live turns here.\n"
                     "Voice and typed requests share one conversation.\n")
        self.error_line = self._label(self.right, "", color=CORAL, size=9,
                                      wraplength=330, justify="left")
        self.error_line.pack(fill="x", padx=20, pady=(4, 4))
        composer = tk.Frame(self.right, bg=STEEL)
        composer.pack(fill="x", padx=17, pady=(0, 17))
        self.command = tk.Entry(composer, bg=STEEL, fg=IVORY,
                                insertbackground=CYAN, relief="flat",
                                font=self._font("Segoe UI", 11))
        self.command.pack(side="left", fill="x", expand=True,
                          padx=(14, 6), pady=13)
        self.command.insert(0, "")
        self.command.bind("<Return>", self._send)
        self.send_button = tk.Button(composer, text="SEND ↗", command=self._send,
                                     bg=CYAN, fg=NAVY, activebackground=IVORY,
                                     activeforeground=NAVY, bd=0,
                                     font=self._font("Consolas", 9, "bold"),
                                     cursor="hand2", padx=12, pady=8)
        self.send_button.pack(side="right", padx=7)
        # Tk pack allocates in request order; let the composer reserve its
        # fixed height before the growing transcript claims the remainder.
        self.chat.pack_forget()
        self.error_line.pack_forget()
        composer.pack_forget()
        composer.pack(side="bottom", fill="x", padx=17, pady=(0, 17))
        self.error_line.pack(side="bottom", fill="x", padx=20, pady=(4, 4))
        self.chat.pack(fill="both", expand=True)

    def _append(self, kind, message):
        self.chat.configure(state="normal")
        if kind in {"user", "assistant"}:
            self.chat.insert("end", ("YOU" if kind == "user" else "JARVIS") + "\n", "author")
            self.chat.insert("end", message + "\n\n", "message")
        else:
            self.chat.insert("end", message + "\n", "error" if kind == "error" else "notice")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _send(self, _event=None):
        text = self.command.get().strip()
        if not text:
            return
        if not self.connection or not self.connection.get("brain"):
            self.error_line.configure(text="Agent offline. Start JARVIS with START-JARVIS-DESKTOP.bat.")
            return
        self.command.delete(0, "end")
        self.error_line.configure(text="")
        self.send_button.configure(state="disabled", text="SENDING")

        def send():
            try:
                self.client.send(text)
                self.ui_queue.put(("sent", None))
            except Exception as exc:
                self.ui_queue.put(("send_error", (text, str(exc))))

        threading.Thread(target=send, daemon=True).start()

    def _schedule_poll(self):
        if self.closed:
            return
        if not self.polling:
            self.polling = True

            def read():
                try:
                    health = self.client.health()
                except Exception:
                    health = {"brain": False, "visualizer": False,
                              "hands": False, "state": "offline",
                              "level": 0.0, "samples": []}
                events = []
                if health["brain"]:
                    try:
                        events = self.client.events()
                    except Exception:
                        pass
                try:
                    overview = self.observability.snapshot()
                except Exception:
                    overview = {"audit": [], "task": None, "files": [],
                                "apps": [], "android": "Local status unavailable."}
                self.ui_queue.put(("poll", (health, events, overview)))

            threading.Thread(target=read, daemon=True).start()
        self.after(850, self._schedule_poll)

    def _drain(self):
        if self.closed:
            return
        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()
                if kind == "poll":
                    self.polling = False
                    health, events, overview = payload
                    self.connection = health
                    self.voice_state = health["state"] if health["brain"] else "offline"
                    self.level = max(0, min(1, health["level"]))
                    self.samples = health["samples"]
                    for service, dot in self.indicators.items():
                        dot.configure(fg=CYAN if health[service] else MUTED)
                    self.status.configure(
                        text="SYSTEM ONLINE" if health["brain"] else "AGENT OFFLINE",
                        fg=CYAN if health["brain"] else AMBER)
                    self.mode_label.configure(text=self.voice_state.upper(),
                                              fg=CYAN if health["brain"] else MUTED)
                    if not health["brain"] or (events and
                            int(events[-1].get("id", 0)) < self.last_event):
                        # A restarted voice owner starts event IDs at one.
                        self.last_event = 0
                    for event in events:
                        try:
                            event_id = int(event["id"])
                        except (KeyError, ValueError, TypeError):
                            continue
                        if event_id > self.last_event:
                            self._append(event.get("kind", "notice"), str(event.get("text", "")))
                            self.last_event = event_id
                    if overview != self.overview:
                        self._render_overview(overview)
                        self.overview = overview
                elif kind == "sent":
                    self.send_button.configure(state="normal", text="SEND ↗")
                elif kind == "send_error":
                    text, error = payload
                    self.send_button.configure(state="normal", text="SEND ↗")
                    self.command.insert(0, text)
                    self.error_line.configure(text=f"Not sent: {error[:130]}")
        except queue.Empty:
            pass
        self.after(80, self._drain)

    def _render_overview(self, overview):
        capabilities = overview.get("capabilities") or []
        if capabilities != self.capabilities_data:
            self.capabilities_data = capabilities
            self._filter_capabilities()
        task = overview.get("task")
        if task:
            steps = task.get("steps") or []
            done = sum(step.get("status") in {"verified", "observed"} for step in steps)
            self.task_line.configure(
                text=f"Mission {task.get('status', 'unknown')}  ·  {done}/{len(steps)} steps observed or verified",
                fg=IVORY)
        else:
            self.task_line.configure(
                text="No task plan yet. Ask JARVIS for a multi-step mission.", fg=MUTED)
        self.activity_text.configure(state="normal")
        self.activity_text.delete("1.0", "end")
        history = overview.get("audit") or []
        if not history:
            self.activity_text.insert("end", "No recorded actions yet.\n", "observed")
        else:
            for event in reversed(history):
                status = event.get("status", "unknown")
                line = (f"{local_time(event.get('timestamp', ''))}   "
                        f"{event.get('tool', 'unknown')}\n")
                self.activity_text.insert("end", line)
                self.activity_text.insert("end", f"             {status}\n\n", status)
        self.activity_text.configure(state="disabled")

        current_files = overview.get("files") or []
        if not self.files_rendered or current_files != self.file_items:
            selected_path = None
            selected = self.file_list.curselection()
            if selected and int(selected[0]) < len(self.file_items):
                selected_path = self.file_items[int(selected[0])]["path"]
            self.file_items = current_files
            self.files_rendered = True
            self.file_list.delete(0, "end")
            if self.file_items:
                for index, item in enumerate(self.file_items):
                    size = max(1, int(item.get("bytes", 0)) // 1024)
                    self.file_list.insert("end", f"{item['name']}   ·   {size} KB")
                    if item["path"] == selected_path:
                        self.file_list.selection_set(index)
            else:
                self.file_list.insert("end", "No reports or presentations saved in JARVIS/output/reports yet.")
        apps = overview.get("apps") or []
        if apps:
            names = ", ".join(item.get("name", "app") for item in apps[:5])
            self.apps_line.configure(
                text=f"Saved apps: {names}. Ask JARVIS to launch one; it will re-check integrity.")
        else:
            self.apps_line.configure(text="No generated apps yet.")
        self.device_line.configure(text=overview.get("android") or "Android status unavailable.")

    def _toggle_motion(self):
        self.motion = not self.motion
        self.motion_button.configure(text="Motion: on" if self.motion else "Motion: off")
        self._draw_core()

    def _animate(self):
        if self.closed:
            return
        if self.motion:
            self.phase += 0.035 if self.voice_state == "idle" else 0.075
            self._draw_core()
        self.after(60, self._animate)

    def _draw_core(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 20 or h < 20:
            return
        x, y = w / 2, h * 0.47
        radius = min(w * 0.35, h * 0.34, 174)
        color = {"offline": MUTED, "idle": CYAN, "listening": CYAN,
                 "thinking": AMBER, "speaking": CYAN}.get(self.voice_state, CYAN)
        for fraction, stroke in ((1.36, STEEL), (1.17, LINE), (0.94, LINE)):
            r = radius * fraction
            c.create_oval(x-r, y-r, x+r, y+r, outline=stroke, width=1)
        for i in range(4):
            r = radius * (1.04 + i * 0.045)
            start = (self.phase * 22 + i * 82) % 360 if self.motion else i * 82
            c.create_arc(x-r, y-r, x+r, y+r, start=start,
                         extent=30 + 5*i, outline=color, width=2+i%2,
                         style="arc")
        pulse = (math.sin(self.phase * 2) * 3 if self.motion else 0)
        r = radius * 0.71 + pulse + self.level * 12
        c.create_oval(x-r, y-r, x+r, y+r, outline=color, width=2)
        r2 = radius * 0.54
        c.create_oval(x-r2, y-r2, x+r2, y+r2,
                      fill="#102A3A" if self.voice_state != "offline" else STEEL,
                      outline=LINE, width=2)
        # Dimensional, restrained core rather than a literal uncanny face.
        for scale, shade in ((0.43, "#164057"), (0.28, "#1D6179"), (0.15, color)):
            rr = radius * scale
            c.create_oval(x-rr, y-rr, x+rr, y+rr, fill=shade, outline="")
        c.create_text(x, y + radius * 0.78, text=self.voice_state.upper(),
                      fill=color, font=self._font("Consolas", 12, "bold"))
        c.create_text(x, y - radius * 1.52,
                      text="J / 02     LIVE SIGNAL", fill=MUTED,
                      font=self._font("Consolas", 9))
        # A small live waveform makes actual speech legible without
        # pretending the core is speaking when the signal is silent.
        count = 32
        baseline = min(h - 20, y + radius * 1.53)
        step = min((w - 45) / count, 11)
        for i in range(count):
            sample = 0.0
            if self.voice_state == "speaking" and self.samples:
                sample = abs(float(self.samples[(i * len(self.samples)) // count])) / 10000
            height = 3 + min(22, sample * 20)
            xx = x + (i - (count-1)/2) * step
            c.create_line(xx, baseline-height, xx, baseline+height,
                          fill=color if sample else LINE, width=2)

    def _close(self):
        self.closed = True
        self.destroy()


if __name__ == "__main__":
    try:
        Cockpit().mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
