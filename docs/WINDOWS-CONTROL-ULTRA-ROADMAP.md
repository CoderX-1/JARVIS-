# Windows Control Ultra - locked implementation roadmap

This is now the Windows adapter track beneath the cross-device master plan in
`JARVIS-OMEGA-ROADMAP.md`. Its remaining gates continue, but shared cognition,
mobile, home/IoT, ambient presence and robotics are governed by the Omega plan.

This document records the requested end-state for JARVIS. Work proceeds one
engine at a time. Each engine must pass automated, native smoke, and user manual
tests before the next engine begins.

## Current gate

**Gate 4 Verification Engine 2.0 and Watchdog: deployed and manually accepted.**
Its four accepted components are universal verification contracts, action
watchdog containment, duplicate-action suppression, and interaction/modal
arbitration. Gate 5 Smart Typing and Semantic Mouse is now active; Component 1
is clipboard-free Unicode typing with focused-control content verification.

The Florence semantic-vision adapter is approved, active, offline, and isolated
from the speech environment. It is a last-resort proposal engine guarded by
label-conflict rejection, two-pass target acquisition, and explicit result
postconditions.

## Capability status

| # | Requested capability | Current status | Remaining work |
|---|---|---|---|
| 1 | Vision-Control Engine | Implemented, deployed and accepted for progression | Continued regression monitoring |
| 2 | UI State Graph | Phase 2 deployed and manually accepted | Continued regression monitoring |
| 3 | Self-Healing Selectors | Deployed: ranked evidence, stable identity, role/context anchors, access-key evidence, fresh repair, bounded decaying memory | User manual acceptance |
| 4 | Advanced Window Management | Partial | Monitor targeting, layouts, virtual desktops, ownership, tray/background/full-screen/hang state |
| 5 | Deep App Reading | Partial | Structured editors, selections, cursor, tables/lists, browser/PDF/forms/status/terminal adapters |
| 6 | Smart Typing Engine | Gate 5 Component 1 deployed: layout typing plus clipboard-free Unicode/emoji SendInput and content verification | Selection/cursor insertion, rich text, verified retry and undo |
| 7 | Semantic Mouse Control | Partial | Sliders, verified drag/drop, range selection, canvas manipulation, user-input arbitration |
| 8 | Process/Application Lifecycle | Partial | Responsiveness/resources/children/crash detection, save-dialog recovery, verified restart |
| 9 | File Explorer Intelligence | Not yet dedicated | Selection/folder state, transactional copy/move/rename/zip/filter/duplicates/recycle restore |
| 10 | Settings and Hardware | Basic volume/media only | Audio devices, brightness, radios, display, power, camera/printer/device state adapters |
| 11 | Notification and Tray Intelligence | Not implemented | Read/classify/watch, download/meeting/system alerts, verified tray interaction |
| 12 | Clipboard Intelligence | Not implemented | Preserve/restore, formats/images/history, secret detection and non-retention |
| 13 | Application-Specific Adapters | Not implemented | VS Code, Explorer, browser, Spotify, WhatsApp, Office, Discord and Settings adapters |
| 14 | Workflow Learning | Not implemented | Semantic demonstration capture, parameterization, validation, versioning and safe replay |
| 15 | Autonomous Task Executor | Basic tool loop only | Outcome planning, dependency graph, replanning, budgets, evidence-backed completion |
| 16 | Verification Engine 2.0 | Strong visual/action subset | Universal per-action contracts, alternate-method recovery, final evidence bundles |
| 17 | Undo and Transaction System | Not implemented | Snapshots, journals, compensating actions, rollback verification and recovery manifests |
| 18 | Windows Watchdog | Partial safeguards | Heartbeat, user-input pause, deadlock/modal detection, duplicate suppression, emergency stop |

## Delivery sequence and acceptance gates

### Gate 1 - Vision-Control Engine

- Current deterministic stack: OCR, enriched UIA, semantic role/position/color
  grounding, local pixel grounding, learned templates, bounded scroll search,
  moving-target stabilization, guarded input and postcondition verification.
- Persistent offline Florence phrase grounding is the final fallback for
  natural descriptions of otherwise-unlabelled visual controls.
- Acceptance: all checks in `VISION-CONTROL-PEAK-AUDIT.md` pass manually.

### Gate 2 - UI State Graph

- Build structured window/control hierarchy.
- Track focused element, active tab, modal ownership, selected values, modified
  state, loading/progress/error conditions and operation state.
- Add expected-state contracts and privacy-safe persistence.
- Test with native harnesses, Calculator, Notepad, Settings and a browser.

### Gate 3 - Self-Healing Selectors and Recovery

- Implemented: generate and score alternative selectors from stable identity, accessible
  name, role, context, shortcuts, OCR, template and guarded geometry.
- Implemented: re-observe before every repair; never repeat an input after it
  may have been delivered; never reuse stale geometry.
- Implemented: learn verified selector strategies per hashed app/version and
  target identity with decay, atomic bounded persistence and no raw UI data.
- Acceptance evidence and manual checklist:
  `SELF-HEALING-SELECTORS-GATE3-AUDIT.md`.

### Gate 4 - Verification Engine 2.0 and Watchdog

- Give every action an explicit observable success contract.
- Add action deadlines, duplicate suppression, modal blockers, user physical
  input pause, guaranteed key/button release and instant stop handling.
- Produce compact evidence for success and honest failure.

### Gate 5 - Smart Typing and Semantic Mouse

- Verified editable-target focus, Unicode input, clipboard preservation,
  selected-text/cursor operations, rich-text paths and rollback on mismatch.
- Verified sliders, drag/drop, resize, canvas and multi-selection actions.

### Gate 6 - Windows and Process Intelligence

- Multi-monitor layouts, virtual desktops, window ownership, tray/background
  apps, responsiveness, resources, child processes, graceful close and restart.

### Gate 7 - Deep Reading and File Explorer

- Structured app content and status reading.
- Transactional Explorer operations with source/destination verification,
  collision handling, undo manifests and Recycle Bin recovery.

### Gate 8 - Settings, Hardware, Notifications and Clipboard

- Dedicated state readers and reversible controllers.
- Never expose passwords, tokens, API keys or protected clipboard content to
  logs, memory, speech or model history.

### Gate 9 - Application Brains

- Add narrow, tested adapters for high-value apps while preserving the
  universal UIA/vision fallback for unknown apps.

### Gate 10 - Workflow Learning, Transactions and Autonomous Execution

- Store semantic workflows rather than coordinates.
- Plan from outcomes, verify each step, replan on changed state and roll back
  completed reversible steps when a later step fails.
- "Complete" means observed end-state evidence, not merely issued commands.

## Non-negotiable engineering rules

- No blind coordinate replay.
- No success without observable evidence.
- No guessing on ambiguity, stale windows, moving targets or protected fields.
- Passwords and secrets are excluded from screenshots, OCR, audit and memory.
- Secure desktop, UAC credential surfaces and lock screens fail closed.
- Routine reversible actions can remain automatic; internal safeguards still
  validate exact targets and preserve recovery information.
- Every phase gets unit regressions, failure-injection tests, a native smoke
  harness and a user-run manual checklist before the next phase starts.
