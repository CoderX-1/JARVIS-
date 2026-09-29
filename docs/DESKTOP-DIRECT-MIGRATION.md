# Direct desktop migration gates

Goal: one Windows JARVIS application with the existing Board visual and Spatial
interaction power, no external browser UI, and no duplicate agent or mic owner.

## Gate A — Direct Board (implemented)

- Mount original Board canvas/HUD in the cockpit Shadow DOM, not an iframe.
- Reuse pinned original Board and visualizer core; proxy only local state/config.
- Keep chat, Activity, Abilities, Files, Android and the same Backtalk bridge.
- Native smoke: canvas styled and painting, Board keyboard focus, Brain live,
  Spatial tab selectable. Compare idle/listening/thinking/speaking visually
  with the original in a real interactive session before retiring source routes.

## Gate B — Spatial functional parity (in progress)

- Implemented: scoped direct renderer, no Spatial iframe; local API proxy;
  mouse-operated ring, orbs, tree, props and command channel without a camera.
- Implemented: local, hash-pinned Three.js, MediaPipe WASM and hand model;
  browser CSP has no CDN dependency. Native WebView2 verified imports and
  GPU-delegated model initialization without a webcam.
- Still requires a real camera: permission, video capture, pinch/drag,
  camera cycling, and long-running tracking/3D performance. Do not call
  those verified merely because no-camera tests pass.
- Still requires sample prop/model tests and an OBS tracker/render role check.

## Gate C — App-grade distribution

- Supervise agent/face/spatial services together without duplicate starts.
- Package runtime/assets, first-run diagnostics, update/rollback, installer,
  signed build, crash reporting, and user-controlled camera/storage settings.
- Benchmark idle CPU/GPU, active gesture FPS, memory, voice-to-reply latency,
  and startup time on the target PC. UI integration alone is not an AI-speed
  improvement.
