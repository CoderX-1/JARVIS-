# JARVIS desktop cockpit — phase 1

The new desktop window is a client of the existing Backtalk voice/agent
process. It does not create a second model session, microphone owner, or tool
registry. Voice (HOME) and typed turns share Backtalk's existing queue and
agent history. The 8790 face and 8794 spatial board remain separate local
services; their signals/status are shown in the cockpit. Open-workspace links
use the Windows default browser. Existing browser/Windows/Android/research
tools remain in the agent core, not copied into the UI.

## What works in this slice

- Native Windows window with responsive AI core, audio waveform, voice state,
  chat transcript, service health, typed mission input, and reduced-motion
  toggle.
- Loopback-only typed-turn bridge at 127.0.0.1:8792. Random per-session token
  stays in the local runtime directory; Origin-bearing requests are rejected.
  Messages are bounded and queued, with overload errors instead of silent loss.
- Optional `START-JARVIS-DESKTOP.bat`; the original launcher and browser mode
  are unchanged. Closing the launcher stops JARVIS. Closing just the cockpit
  closes the window, not the voice agent.

## Not yet complete

- The spatial board and browser are not embedded in the native window.
- Artifact previews, Android device dashboard, mission timeline, and
  verification/evidence panels are not yet present.
- No packaged installer or signed executable. The launcher uses the existing
  Python 3 Tk runtime.
- Real provider-backed live voice/desktop integration has not been exercised
  by this phase's tests; a mock bridge verified the UI and typed-turn path.

## Automated evidence

- `python -m unittest test_desktop_bridge -v`: 3 pass.
- Live Backtalk/core suite: 134 pass; root suite: 28 pass.
- `python desktop_ui_smoke.py`: real Windows window, local mock bridge,
  typed send, reply render, screenshot visual QA passed.

Next phase should embed or safely dock browser/spatial workflows, add a
verified action timeline, artifact viewer, and Android device state without
creating a second agent. Keep all secrets and tool execution in the core.
