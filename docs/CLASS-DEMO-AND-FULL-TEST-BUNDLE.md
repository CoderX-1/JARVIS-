# JARVIS class demo and full acceptance bundle — 30 September 2026

This is an operator guide, not a certification that every feature is working
on every PC. Use the native Board cockpit. Its localhost ports are internal
plumbing; do not present them as the product UI. Never display `.env`, API
keys, passwords, private messages, or live Gmail during class.

## What the system is, in plain language

The microphone/Home key (or the app's chat box) supplies a request. Speech
recognition turns audio into text. OpenAI/Gemini provider routing supplies
reasoning; the tool registry lets the model propose an action. JARVIS's
executor checks exact targets and permissions, performs bounded actions, then
observes the result. The app displays real conversation, health, activity,
abilities, files, and the Board/Spatial visualizer. Fish/Gemini synthesize the
spoken reply. A tool appearing in Abilities means registered, not necessarily
configured or manually proven on this machine.

## Current truth before class

- Native Board app, text chat, voice route, desktop window/app controls,
  read-only PC diagnostics, web source reads, evidence PDF, and editable PPTX
  have automated or limited live evidence. The browser is not required to
  display JARVIS; a browser may open only when explicitly controlling websites
  or opening a link.
- PPTX structural checks pass, but native PowerPoint visual acceptance is
  pending. This PC has no `.pptx` default viewer. On the presentation PC,
  check PowerPoint/LibreOffice ahead of time, or upload to OneDrive and use
  PowerPoint for the web. Never claim visual PPTX QA passed here.
- Dedicated editable DOCX writing is not yet built. Existing DOCX files can
  be indexed; this is different from generating a polished DOCX.
- Android ADB is not installed/paired on this PC; phone control is not a demo
  claim. Spatial mouse mode works without a camera; gestures are untested.
- Supabase login code is staged but not enabled until credentials and an
  end-to-end login test pass. Gmail now has an offline, default-off reply
  eligibility policy; OAuth/inbox/AI drafting/sending/notification and the
  installer are not shipped.
- App Foundry executes generated Python without an OS-level sandbox; do not
  demo it with untrusted code. Research findings still need human source check.

## Before the audience arrives

1. Use the real interactive Windows desktop. Connect stable internet, mic,
   speakers, and power. Disable distracting Windows notifications. Have a
   backup video/screenshot and a locally saved PDF; live services can fail.
2. From `C:\Projects\JARVIS`, launch
   `powershell -NoProfile -ExecutionPolicy Bypass -File .\RUN-JARVIS.ps1 -Desktop`.
   Keep that PowerShell window open. Do not run a second copy of voice.
3. In the Board app, confirm **Brain connected**, Board animation, and typed
   chat. If Supabase gate is enabled, sign in with the one pre-created account.
   Cancel/wrong password must leave JARVIS services stopped.
4. Hold HOME, speak clearly for 3–6 seconds, release, and read the displayed
   transcript before judging the answer. If accent or STT is poor, switch to
   the chat box; it uses the same assistant session.
5. Check one PDF opens. Check a PPTX viewer on the exact presentation PC.
   Test the projector resolution. Do not depend on live install during class.

## Recommended 8–12 minute live script

Say the text naturally or paste it into the right-hand chat box. Wait for
visible verification before making the next request. Do not claim an action
worked just because JARVIS said it did.

1. **Voice + face (1 min):** “Jarvis, introduce yourself in two short
   sentences and tell me what you can actually do on this computer.” Show
   listening → thinking → speaking and the real transcript. If Urdu sounds
   wrong, use English for the demo; say accent tuning is in progress.
2. **Read-only PC awareness (1 min):** “Check my PC diagnostics: CPU, memory,
   drive space and battery. Clearly say which sensors are unavailable.” Show
   the result and Activity status. Temperature/fan may be unavailable.
3. **Desktop action (1 min):** “Find Calculator and open it. Verify its window
   appeared.” Then: “Close the Calculator window gracefully and verify it is
   gone.” If Calculator is absent, use Notepad but close before typing.
4. **Source-backed research (1–2 min):** “Inspect
   https://www.iana.org/domains/reserved and tell me what the page actually
   says about example domains, with the source URL.” Explain that JARVIS reads
   the original public page; it does not treat a model's memory as a source.
5. **Professional PDF (1–2 min):** “Create a concise professional PDF brief
   from https://www.iana.org/domains/reserved and
   https://www.rfc-editor.org/rfc/rfc2606 about reserved example domains.
   Include exact citations and save a new file.” Open it from **Files** and
   show source links. If network fails, use the pre-generated backup PDF.
6. **PPTX (1 min):** “Create an editable, source-attributed PowerPoint
   presentation from those same two URLs, with concise findings and a
   sources slide. Save a new file.” Show the `.pptx` entry in Files. Only
   open/project it if PowerPoint/LibreOffice on the demo PC has been tested.
   The generated deck is editable text, not a screenshot.
7. **Verification + limits (1 min):** Open Activity and Abilities. Explain
   “registered tool” versus “verified result.” Open Spatial in mouse mode;
   show the ring/orbs without claiming camera hand tracking. End with:
   “It plans, acts through tools, checks outcomes, and reports limits; it is
   not a conscious or unrestricted movie AI.”

Do not demo Gmail auto-send, Supabase login, Android phone control, a new
installer, or polished DOCX until each feature's own real acceptance passes.

## Consolidated manual acceptance matrix

Record each result as PASS / FAIL / NOT TESTED, date, exact machine, and a
sanitized screenshot or audit entry. Stop and report the first failure; do
not silently skip or call the whole release “100%”.

| Area | Test | Pass means |
| --- | --- | --- |
| Startup | Launch desktop once, try a second launcher, close first | One mic/Home owner; no orphan services or extra browser UI |
| Supabase | Correct password, wrong password, close sign-in, offline | Only allowed account starts services; failures start none |
| Voice input | 10 English + 10 Roman Urdu phrases, silence, fast/slow speech | Correct transcript or explicit failure; no stuck listening |
| Voice output | 5 English + 5 Roman Urdu replies, Fish outage/fallback | Audible, stable voice, user rates accent and latency; no mute |
| Chat | Type, Enter, Shift+Enter, long reply, restart | One conversation session, no duplicate action |
| PC | Diagnostics including unsupported sensors | Real measurements and honest unavailable labels |
| Apps/windows | Open/close installed app; ask for nonexistent app; two windows | Exact target, observed after-state, no blind force-kill |
| UI/vision | Inspect a named control, find text, click, stale target, modal | Fresh observation and correct refusal/retry; no password capture |
| Browser | Use default browser, navigate, read page, interact | Actual URL/title/visible postcondition; no wrong-browser assumption |
| Knowledge | Index one chosen PDF/DOCX/PPTX, search late passage, forget | Page/slide locator, stale withholding, original unchanged |
| Research | Check an original source, false quote, unsafe private URL | Exact quote only when present; unsafe URL refused |
| PDF | New cited report, inspect pages/links, repeat same path | Readable file, sources, no overwrite |
| PPTX | New deck, open/edit in PowerPoint/LibreOffice, check links | No repair warning/clipping; editable text and correct URLs |
| DOCX | Create polished dedicated document | NOT READY; do not mark pass |
| Spatial | Mouse mode, then real camera only if available | No-camera status honest; hand gestures separately proven |
| Android | Exact paired serial, installed package, foreground, disconnect | NOT READY here until official ADB + phone acceptance |
| Workflows | Repeat verified workflow, inspect/disable learned hint | No raw prompt saved; every replay re-observes state |
| Gmail | OAuth connect, dry-run, allowlisted auto-reply, duplicate/race | NOT READY; no mail sent until separate consent and tests |
| Installer | Clean PC, no bundled secrets, login, restart, uninstall | NOT READY; distribution gate last |

For automated checks, source core: `python -m unittest discover -s tests -p
'test_*.py' -q` from `C:\Projects\fullstack-agent-main\.jarvis-publish\core`.
Live core: same command from `C:\Projects\JARVIS\core`. These do not prove
microphone, projector, PowerPoint, OAuth, or another laptop works.
From `C:\Projects\fullstack-agent-main`, run
`python board_app_headless_smoke.py --http-only` to verify the local app shell
HTML/JS endpoints. The optional full headless Edge rendering path currently
fails in this machine's GPU process (crash/timeout), so visual WebView2
acceptance remains a separate manual test, not a false pass.

## If something fails on stage

- Voice fails: type the same prompt in the app. Never keep pressing HOME while
  it is processing. Show Activity rather than claiming a spoken result.
- Source/PDF fails: show the earlier generated report and name the network/API
  limitation honestly. Do not retry an existing filename.
- PPTX does not open: show its file entry and use a pre-tested PowerPoint PC or
  OneDrive/PowerPoint for the web. No local viewer does not disable JARVIS.
- Board says Brain offline: do not demo tool actions. Restart once using the
  launcher, then use the backup video if needed.

## Next engineering gates after this demo

1. Finish live Supabase setup and validate login/startup/offline behavior.
2. Record and rate Pakistani Roman Urdu voice samples; choose a suitable
   reference voice/model, then verify accent and latency over repeated turns.
3. Finish DOCX authoring; visually inspect PPTX in a native viewer and fix
   any layout defects; finish the remaining research and device gates.
4. Build Gmail OAuth inbox adapter with sender rules, draft/dry-run, duplicate
   suppression, sent-mail verification, and notification/audit. Auto-send is
   disabled until the owner approves exact scope and test messages.
5. Run the full manual matrix on the target PC, then build/test a Windows
   installer without secrets. A signed build and clean-machine acceptance are
   separate tasks from making a ZIP of source code.
