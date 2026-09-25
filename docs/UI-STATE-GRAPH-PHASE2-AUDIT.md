# UI State Graph Phase 2 — implementation and acceptance report

## Outcome

Phase 2 is implemented, deployed, and has passed automated and native read-only
tests. It is not a claim of general intelligence or consciousness. It is the
world-model layer required for a dependable JARVIS control loop: fresh state,
explicit expectations, truthful verification, and privacy-safe history.

Gate 3 remains locked until the user completes the manual checks below and says
that the UI State Graph manual test passed.

Latest deployment backup: `C:\Projects\JARVIS\runtime\backups\ui-state-graph-20260914-170832`.
The restarted runtime exposes 40 tools, including both new state tools. Ports
8790, 8791, 8794, and 8795 are listening; deployed/source hashes match; all
runtime error logs are empty. A deployed expected-window contract passed against
the live Settings surface, and the persisted graph is schema v2 with no raw UI
content keys.

## What changed

- Upgraded persistent graph schema from v1 fingerprints to v2 structured state.
- Added safe v1 migration on the next normal mutation. Corrupt or unsupported
  files remain untouched and persistence fails closed.
- Added stable control identities and parent/child hierarchy from UI Automation
  runtime IDs.
- Added live focus, active tab, selection, toggle, expand/collapse, value-present,
  modal, window interaction, progress, modified, error, and operation state.
- Added `inspect_ui_state`, a read-only tool that gives the planner a fresh state.
- Added `verify_ui_state`, a read-only expected-state contract evaluator.
- Added `expected_state` to verified visual clicks. An action cannot use a state
  that was already true as proof unless fresh evidence also shows a transition.
- Attached only contract hashes and pass counts to transition history.
- Added portable UIA extraction and removed an unavailable legacy .NET pattern
  that could silently discard every element on this Windows installation.
- Updated the runtime agent contract to use perceive/model/plan/guard/act/verify/
  recover and to distinguish facts, inference, and unknown state.

## Privacy and safety properties

Persistent state contains no screenshots, OCR text, window titles, control
labels, target labels, field values, or raw contracts. Runtime audit records
redact live state output and expected-state objects. Password controls are still
excluded before UI state extraction. The graph does not grant permission and
does not autonomously replay old actions.

## Automated evidence

Commands:

```powershell
python -B -m unittest discover
python -B -m unittest discover -s tests
```

Result on 2026-09-14: **118 passed** (90 advanced/desktop tests plus 28 core,
provider, permission, registry, and speech tests).

Coverage includes schema migration, corruption preservation, bounded storage,
hierarchy, focus, active tabs, progress and operation derivation, positive and
negative contracts, closed-window contracts, click integration, privacy leak
scans, audit redaction, tool routing, failover, permissions, speech, stale target,
occlusion, Florence guardrails, and all prior regressions.

## Native Windows evidence

Command (run with JARVIS's environment):

```powershell
& 'C:\Projects\JARVIS\components\backtalk\.venv\Scripts\python.exe' -B ui_state_graph_live_test.py
```

Read-only native results:

- Notepad: state captured; hierarchy roots and focused control detected.
- Calculator: framed app state captured; controls and actionable controls found.
- Settings: structured hierarchy and focused control captured.
- Brave: 154 controls, 116 actionable controls, active tab and focus detected.
- Persistence parsed as schema v2 and raw title privacy checks passed.

The smoke uses temporary storage and does not type, click content, close windows,
or retain raw UI content.

## Honest limitations

- State quality is limited by what each application exposes through Windows UI
  Automation. Canvas/game/remote-desktop surfaces still require the Vision engine.
- `modified` is currently an evidence-backed title marker inference (`*`,
  `modified`, or `unsaved`), not a universal document API.
- Generic error classification uses explicit accessible labels. Application-
  specific error/status adapters belong to later gates.
- Modal ownership is available when the application exposes WindowPattern. Some
  custom frameworks hide it.
- The state graph is not yet a self-healing selector engine. That is Gate 3.

## Manual acceptance tests

Keep Notepad, Calculator, Settings, and a browser open. Hold HOME, speak, then
release. After each test, wait for the spoken answer before starting the next.

1. Say: `Jarvis, inspect the current UI state and tell me the focused control,
   active tab, modal state, and operation state.`
   Expected: it calls the state inspection tool and reports observed values; it
   must not click or type.
2. In the browser, select a clearly named tab. Say: `Verify that the active tab
   is <exact tab name>.`
   Expected: `Verified UI state contract`. Repeat with a deliberately wrong tab
   name; expected: an explicit contract-not-satisfied error.
3. In Settings, say: `Inspect Settings and tell me how many controls are
   actionable and whether a modal is present.`
   Expected: fresh structured counts; no interaction.
4. In Calculator, say: `Verify Calculator is idle and its Calculator window is
   present.`
   Expected: both checks pass or JARVIS truthfully reports which condition did
   not pass.
5. Open a harmless dialog such as Notepad's Find dialog. Say: `Inspect Notepad
   and tell me whether a modal is present and what control has focus.`
   Expected: the exposed modal/focus state is reported. Some Notepad versions
   expose Find as a pane rather than a modal; either answer is acceptable only
   if it matches the live UIA evidence.
6. Say: `Show UI State Graph status`, then `Show recent UI transitions.`
   Expected: schema v2, structured model capabilities, privacy flags, and no raw
   private titles or labels in history.
7. Say: `Click <a harmless tab> and verify that tab becomes selected.`
   Expected: JARVIS uses an `expected_state` contract and claims success only
   after the selected tab is observed. Use only a reversible test tab.

If any result is wrong, note the exact spoken request, visible app state, and
JARVIS reply; do not approve Gate 3 yet.
