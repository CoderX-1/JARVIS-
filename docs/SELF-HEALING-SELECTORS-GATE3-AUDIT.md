# Gate 3 — Self-Healing Selectors: implementation and acceptance

## Outcome

Gate 3 is implemented and deployed and has passed automated, native Windows,
runtime registration, file-integrity, HTTP and four-port acceptance. It remains
blocked from Gate 4 until the user completes the manual checks in this document
and explicitly confirms they pass.

## What changed

- `selector_engine.py` adds deterministic selector ranking and repair.
- Stable UIA runtime/automation identity outranks weaker visual evidence.
- Exact OCR remains a fast path. If it disappears on the required fresh
  observation, UIA, semantic, enhanced OCR, template, pixel, or local-VLM
  evidence can replace it without stale-coordinate replay.
- `role` and `anchor` are typed optional inputs for `find_visual_target`,
  `click_visual_text`, and `click_visual_target`.
- Structural anchors use current UIA parent identity to resolve duplicate
  labels. They do not persist their raw label.
- Accessibility access keys are scored as alternative identity evidence. The
  selector engine never presses them by itself; input remains in the existing
  guarded invoke/click pipeline.
- WinForms controls misreported as `Pane` recover their semantic role from the
  native class, while retaining normal foreground, geometry and occlusion
  checks.
- Every click rebuilds the selector from a fresh observation. Stable identity
  may repair a moved control; a still-moving target is refused.
- After input is delivered, JARVIS only verifies the result. It never issues a
  blind second click, preventing duplicate actions.
- Verified successes and failures update a bounded selector strategy memory.

## Privacy and durability

The durable file is `.jarvis/selector-memory.json`. It stores only:

- hashed app/version identity;
- hashed target/role/anchor identity;
- selector strategy name;
- decaying success/failure counters and update time.

It never stores raw process names, paths, app/window titles, target queries,
anchors, accessibility labels, OCR, screenshots, coordinates, or secrets.
Memory is capped at 512 records, written atomically, decays with a 30-day
half-life, and preserves a corrupt file for diagnosis before recovering.

## Automated evidence

Full repository regression command:

```powershell
cd C:\Projects\fullstack-agent-main
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest test_audit_regressions.py test_florence_client.py test_intelligence.py test_selector_engine.py test_speech_mouth_overlay.py test_ui_state_graph.py test_windows_control.py tests.test_agent tests.test_mark2 tests.test_patch_backtalk tests.test_speech_router
Remove-Item Env:PYTHONDONTWRITEBYTECODE
```

Result after the hosted-Calculator repair: **136 tests passed**, including the
12 focused Gate 3 selector tests and new wrapped-error/hosted-process
failure-injection regressions.

Native Windows harness:

```powershell
cd C:\Projects\fullstack-agent-main
& 'C:\Projects\JARVIS\components\backtalk\.venv\Scripts\python.exe' selector_engine_live_test.py
```

Native result:

- contextual duplicate-label selector: PASS;
- stable-identity repair after target movement: PASS;
- stale coordinates not reused: PASS;
- one click and explicit postcondition: PASS on first verification attempt;
- hashed-memory privacy scan: PASS;
- temporary window cleanup: PASS.

## Live deployment evidence

- Backup: `C:\Projects\JARVIS\runtime\backups\self-healing-selectors-20260915-052129`
- Source/runtime SHA-256 equality: PASS for `jarvis_mark2.py`,
  `windows_vision.py`, and `selector_engine.py`.
- Tool registration: `selector_engine_status=True` and read-only classification
  `True` in the deployed runtime.
- HTTP shell: `http://127.0.0.1:8790/` returned status 200.
- Local listeners ready: 8790, 8791, 8794 and 8795.
- Launcher error log: empty; launcher reported `JARVIS is ready`.

## 2026-09-19 manual-test repair

The first user Calculator run exposed two integration defects, both repaired:

- Calculator's accessibility element belongs to its packaged child process
  while the visible guarded HWND belongs to `ApplicationFrameHost.exe`.
  A process mismatch that explicitly delivered no action now returns an
  `unsupported` result, allowing the independently guarded physical-click
  fallback. Protected/offscreen/disabled/occluded cases still fail closed.
- A wrapped result such as `scroll_search=0; error: ...` was incorrectly marked
  successful because audit/recovery checked only the first characters. Visual
  wrappers now propagate a canonical leading `error:`; shared classifiers also
  recognize nested errors. `denied` remains an audit failure but never triggers
  autonomous recovery.

Deployed acceptance against real Windows Calculator:

- `Seven` located through UIA stable identity: PASS;
- one guarded action delivered after fresh stable-identity revalidation: PASS;
- explicit `Display is 7` postcondition: PASS on attempt 1;
- missing template returned canonical error and `no click was delivered`: PASS;
- audit recorded verified click `success=true` and safe miss `success=false`:
  PASS;
- selector memory created one hashed strategy record with verified successes,
  zero failures, and no raw Calculator/Seven/display text: PASS;
- source/runtime hashes matched for all four repaired files: PASS;
- repair backup:
  `C:\Projects\JARVIS\runtime\backups\gate3-manual-repair-20260915-053931`.
- final restart on 2026-09-19: ports 8790, 8791, 8794 and 8795 ready;
  launcher error log empty.

## Manual acceptance checklist

Run these only after deployment/restart reports all four ports ready.

1. In JARVIS say: `Tell me the self-healing selector engine status.`
   Pass: it reports ready, fresh revalidation required, blind retries disabled,
   memory bounded to 512, and privacy excludes labels/OCR/titles/coordinates.

2. Open Calculator in Standard mode. Say:
   `Find the Seven button in Calculator without clicking it.`
   Pass: JARVIS reports one live target, a selector strategy and selector score;
   Calculator does not change.

3. Resize or move Calculator. Say:
   `Click Seven in Calculator and verify that the display changed to seven.`
   Pass: display becomes 7 and JARVIS reports verified action. The result should
   include `selector=` and `repair=` evidence, not merely “click sent.”

4. Clear Calculator, resize it differently, and repeat step 3.
   Pass: it still finds the current control location; it does not click the old
   screen position and selector status shows at least one verified success.

5. Open any app containing two controls with the same visible label. Ask only
   for that label, without a position, role, occurrence, or anchor.
   Pass: JARVIS refuses the unresolved ambiguity and delivers no input.

6. Repeat with unambiguous context, for example:
   `Find the Open button under the Work panel, role button, without clicking.`
   Pass when the app exposes that hierarchy: only the anchored control is
   returned. If the chosen app has no accessible hierarchy, JARVIS must say it
   cannot resolve it; it must not guess.

7. Start an action on a harmless button, then cover the target with another
   window before delivery.
   Pass: JARVIS reports changed foreground/occlusion and says no click was
   delivered.

8. Inspect `C:\Projects\JARVIS\.jarvis\selector-memory.json` after a verified
   action.
   Pass: it is JSON containing hashes/counters/strategy names only. Your spoken
   target, app title, OCR text and coordinates are absent.

When every applicable check passes, reply exactly or naturally with:
`Gate 3 manual tests passed.` Only then may Gate 4 begin.
