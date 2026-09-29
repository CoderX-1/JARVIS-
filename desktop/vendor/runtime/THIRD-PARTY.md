# Desktop Spatial runtime assets

These are pinned copies used by the local desktop application, not code
written by JARVIS.

- Three.js 0.160.0: `three/`, MIT license in `three/LICENSE`.
- MediaPipe Tasks Vision 0.10.14: `vision/`, Apache-2.0 as declared in
  `vision/package.json`.
- MediaPipe hand-landmarker float16 model: `model/hand_landmarker.task`,
  downloaded from Google's MediaPipe model storage path
  `mediapipe-models/hand_landmarker/hand_landmarker/float16/1/`.

The barehands renderer itself remains AGPL-3.0-or-later and retains its
source attribution. Before redistributing a packaged installer, review the
model's redistribution terms and include any additional required notices.
Every executable/runtime asset is SHA-256 pinned by the desktop server.
