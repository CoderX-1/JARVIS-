# JARVIS Board cockpit

The `-Desktop` launcher opens a native WebView2 window. The **original Board
renderer** is mounted directly in the app's scoped stage, without a Board
iframe or a rewritten canvas algorithm. The direct adapter pins the original
Board/core revisions and reuses their rendering code. The original Spatial
stage is also mounted directly in an isolated Shadow DOM, without an iframe.
Without a camera it runs mouse mode: ring, orbs, note/prop trees, drag, scroll,
and the command channel remain usable. Hand tracking still requires a camera
grant and real-device gesture testing. Other tabs read the same live
Backtalk session through the localhost bridge; the app does not own another
microphone or construct another agent.

## Launch

From `C:\Projects\JARVIS`, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\RUN-JARVIS.ps1 -Desktop
```

Use the logged-in interactive Windows desktop. Hold HOME to speak. Type in the
right-hand composer to send to the same session. Board's own face server is on
127.0.0.1:8790; the cockpit shell chooses a random 127.0.0.1 port and uses a
per-launch session token. The shell never passes provider secrets to the UI.
If voice is already running, the same command opens only a Board cockpit and
attaches to that session; it never starts a second microphone owner.

## Check it manually

1. Confirm the center matches the original Board at
   `http://127.0.0.1:8790/faces/board/`. It should animate through idle,
   listening, thinking, and speaking when the same voice process changes state.
2. Hold HOME, say a short phrase, release. The right-hand chat should show the
   recognized user text and the actual JARVIS reply when Backtalk publishes it.
   If the connection says Brain offline, do not treat a decorative face as a
   successful agent test.
3. Type a safe query such as `What time is it?` and press Enter. Shift+Enter
   must insert a newline. The Send action should enter the same voice session;
   it does not call a separate model.
4. Select Activity. Confirm recent tool records show actual status (verified,
   observed, delivered, failed, denied, unknown), not invented successes.
   Scroll the list, wait several seconds, and confirm periodic status refreshes
   do not jump the scroll position back to the top.
5. Select Abilities and search. These are installed tool registrations, not a
   promise that every provider or device is configured.
6. Select Files and Android. Reports open only when clicked; phone readiness
   says what is configured, not that a phone was actually contacted.
7. Select Spatial. With no camera, click the ring, then an orb, then a note or
   prop row; drag an item and use the wheel to scroll. The status must say
   `Mouse mode — camera off`, not `Hand tracking active`. If you later attach a
   camera, select `Try hand tracking`; only then grant permission and verify
   pinch, drag, camera cycling, notes, props, and a 3D model. A successfully
   loaded preview or initialized model is not proof that gestures work.
8. Closing the desktop window should not leave a second microphone process.
9. Press Ctrl+L and confirm the chat composer gains focus.

If the native window fails, inspect `runtime/logs/desktop-error.log`. The
system requires Microsoft's WebView2 Evergreen Runtime. The legacy circle/Tk
prototype remains at `desktop/app.py` only as an inactive recovery artifact;
`-Desktop` runs `desktop/board_app.py` and never launches the circle UI.

## Boundaries

Only report-shelf files can be opened by this shell; there is no external
browser-opening action. Generated app bundles do not launch from Files; their
integrity checks remain in the agent's app launcher. The direct Board code is
version-pinned and receives no Python API object. A closed face server causes
an explicit offline state. The Spatial source is version-pinned and scoped in
the app; its API requests are proxied to the original loopback service. The
app does not expose its Python object to renderer JS. Three.js, MediaPipe WASM
and the hand model are bundled locally with pinned hashes, so these resources
no longer need a CDN. Native smoke confirmed no-camera ring/orb/tree navigation
and local model/WASM initialization. Physical camera gesture parity, model
rendering with a real prop, and packaged installer testing remain open gates.
