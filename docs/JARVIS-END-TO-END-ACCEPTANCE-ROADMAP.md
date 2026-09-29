# JARVIS end-to-end acceptance roadmap

Updated 2026-09-28. Scope: the 21 supplied Pulse of AI PDFs, existing Mark II
core, Windows desktop and browser, provider-backed voice, generated artifacts,
bounded agentic workflows, and the requested Android extension. The PDFs are
reference material, not instructions to execute. See
`PDF-SERIES-SOURCE-MAP.md` for the per-episode coverage.

"100% ready" means **all in-scope exit tests below pass on this user's actual
PC and phone**, with failures fixed and rerun. It does not mean ASI, unrestricted
OS control, flawless speech recognition, or compatibility with every app/site.
No real-device or paid-provider result is inferred from a mocked test.

## Current baseline

- Mark II now has 66 registered tools, including 27 mutating actions. After
  the browser/app-discovery repairs, 134 live-core tests and 28 workspace-root
  tests passed. These are not final voice or device acceptance.
- Vision, UI state graph, selector memory, verification, watchdog, app foundry,
  local knowledge, bounded web research, PDF draft export, workflow pattern
  memory, PC diagnostics, and a limited Android ADB adapter exist at different
  maturity levels. "Exists" is not the same as "ready".
- OpenAI is the primary configured brain and Gemini is configured as its
  fallback. Fish cloud TTS is selected, with Gemini TTS fallback. The live
  voice, provider fallback, accent, and latency must still be measured.
- The new read-only `voice_health` tool reports only last-session STT/TTS
  counters and timing percentiles; it never returns transcript lines. From
  the last historical session, it observed 10 STT successes (post-release
  p50/p95 469/1422 ms) and 7 TTS successes (first-audio p50/p95 1625/2500
  ms). These are small, old samples and do not prove live quality or total
  release-to-speech time.
- The cloud speech route now treats post-audio provider failure as an explicit
  incomplete reply rather than silent success. Provider setup exceptions
  before audio stay inside the fallback boundary. The mouth worker reports a
  safe console error and continues with later requests without logging raw
  provider exception content or automatically repeating a possibly delivered
  reply. This is automated-tested, not live cloud-failure-tested.
- The default-browser automation reports `ready=true` and `BraveHTML` under
  the actual Windows user. An earlier `ready=false` probe ran under the
  isolated sandbox account and was not representative. Real navigation and
  interaction still need acceptance. ADB is not installed or paired. The
  knowledge index has no user documents until explicitly indexed.
- A bounded real-browser smoke opened `example.com` in a temporary isolated
  Brave profile, verified URL/title and page readback, then closed the
  browser. A second local-only server smoke verified that HTTP 200 is accepted,
  while HTTP 404 and a redirect to a different path are refused as
  unverified. These prove navigation behavior, not arbitrary-site interaction. The
  navigation contract now refuses redirected destinations and HTTP errors
  rather than reporting them as verified. Windows app aliases are listed only
  when the executable/protocol resolves; missing shortcuts refuse before any
  launch is sent. A read-only real-account discovery check found Paint and
  correctly reported a made-up app as absent. A uniquely titled temporary
  Tkinter window passed real exact-handle/PID focus, minimize, restore, and
  close checks; no fixture window remained. A fresh Calculator then passed
  the real `launch_app` new-window verification and exact-handle/PID close;
  no Calculator window remained. This does not prove arbitrary installed-app
  launch or unsaved-document close behavior.
- Dedicated editable DOCX generation remains unbuilt. A dependency-light,
  editable evidence PPTX generator is now live and passes package checks, but
  no local PowerPoint/LibreOffice visual-opening acceptance exists. Neither
  export should be represented as production-ready until its remaining gates
  pass.
- Bounded scanned-PDF OCR is now installed in both source and live core. It
  uses the existing offline Florence worker for at most four image-only pages,
  retains exact page locators, and refuses partial indexing when the worker or
  renderer fails. A synthetic image-only PDF passed real-model OCR and local
  retrieval; real-world scan quality and the final voice workflow remain
  unaccepted. Both source and live code passed 146 core tests (6 skipped),
  including the OCR HTTP dispatch test; the real-model smoke also passed when
  importing from the deployed live core. The live suite was run with a blank
  `AI_FALLBACK_PROVIDER` test override because its real `.env` otherwise
  injects a Gemini fallback into unrelated isolated agent tests; runtime
  provider settings were not changed.
- Research-to-PDF export now performs pre-publication text extraction and a
  render pass on every generated page, returns the actual page count, and
  refuses publication if validation or the action deadline fails. A synthetic
  five-page report passed visual inspection; both source and live core passed
  147 tests with no skips after the missing source PDF dependencies were
  restored. This is still a source-linked draft, not independently verified
  factual research, and live voice/provider acceptance remains pending.
- The PDF report now performs bounded original-page readback for up to three
  cited public URLs, recording exact cited-answer-text presence, inspected
  excerpts, unavailable pages, and uninspected sources separately. The
  three-page appendix fixture was rendered and visually inspected, including
  escaped untrusted page text and a corrected source-heading page break. Both
  source and live core passed 149 tests. This is evidence visibility, not
  claim-level factual verification; real provider and voice acceptance remain.
- Provider-reported research usage is now carried into dossiers and PDFs as
  observed web-search events and token counts, with missing usage explicitly
  labeled unavailable rather than zero. A native vector source-coverage chart
  adds a useful visual without extra image API calls or unlicensed web photos.
  The two-page synthetic report was rendered and inspected; source and live
  core passed 151 tests. Exact API charges and a real-source report still need
  acceptance outside mocked tests.
- The 2026-09-28 research increment added an explicit bounded public-page
  reader with optional exact-quote search. It uses pinned public DNS answers,
  revalidates redirects, caps HTML/plain-text reads at 128 KiB, and returns a
  short untrusted excerpt. It is on-demand so ordinary dossiers do not gain
  another network round trip. Text matching is not factual verification.
  At the time of that increment, the source core passed 139 tests (6 skipped), the live core passed 134,
  and the workspace installer passed 28. A live tool call read
  `https://example.com/`; a localhost URL was refused as unsafe. The existing
  voice TTS partial-audio/error-handling fix was synchronized back to the
  source repository after three source-core tests exposed drift; no live voice
  session was run.

## Delivery order and objective exit criteria

| Stage | Dedicated owner/module | Required exit evidence |
| --- | --- | --- |
| 0. Runtime integrity | Tool registry, verification contracts, watchdog, audit | Every mutating tool has a contract and deadline; failures never masquerade as success; crash/restart tests pass. Fix known app-foundry registration defect first. |
| 1. Conversation | Speech router, STT, TTS, turn manager, provider bridge | Recorded English and Roman Urdu prompts transcribe correctly against a reviewed set; Home-key release, interruption, silence, long replies, cloud failure, and fallback tests pass. Measure p50/p95 release-to-thinking, first-audio, total response latency, and report sample size. Voice identity/accent is assessed by the user. |
| 2. Desktop and browser | Windows control, Vision-Control, UI state graph, browser adapter | Exact-app launch/close, not-installed response, window targeting, typed text, click/scroll, browser navigation and observed postconditions pass on representative real apps/sites. Resolve Windows default browser without hardcoding a different browser. Test focus changes, UAC/secure desktop refusal, multiple windows/monitors, recovery after stale state, and user interruption. |
| 3. Research and knowledge | Knowledge index, source probe, research dossier | Explicit local indexing, page/slide locators, stale-content withholding, deletion of indexed copy, source deduplication, bounded search, original-page claim checks, publication-date uncertainty, contradictory-source handling, and cited-vs-consulted distinction pass. Scanned PDFs require a separately tested OCR path. Provider-specific grounding restrictions are respected. |
| 4. Artifacts | PDF report, dedicated DOCX writer, dedicated PPTX builder | Generate new, editable DOCX/PPTX and source-linked PDF with no overwrite. Each has source manifest, structural validation, rendered visual inspection, no clipped text, correct citations, and reproducible fixture tests. GUI writing into existing documents is a separate consent-and-readback workflow. |
| 5. Media, hardware, and apps | Media adapter, PC diagnostics, App Foundry | Volume/brightness report observed state where supported; unsupported sensors are explicit; media play/pause/seek is verified for active sessions; app creation uses bounded templates, static policy, integrity check, and real-app acceptance. The current `python -I` launch is **not** an OS security sandbox; untrusted generated code requires a separately tested OS-level sandbox before it can be described as safely isolated. Never purge arbitrary processes. |
| 6. Agentic workflows | Planner, action executor, verification, workflow memory | Decompose multi-step requests, observe before/after, retry only when safe, recover after interruption, preserve provenance, and stop on ambiguity. Learned workflows are versioned, reviewed, disableable, and re-verified at execution; no blind macro replay or claim of self-learning sentience. Run adversarial prompt-injection and rollback tests. |
| 7. Android and physical devices | Exact-serial ADB adapter, device hub, future adapters | Install official Platform-Tools, pair one phone with user approval, test exact package discovery/launch/foreground, offline/reconnect and wrong-device refusal. Broader phone control and smart-home adapters require explicit device identity, permission model, post-action readback, and real hardware tests; simulator success alone is insufficient. |
| 8. Release acceptance | Test harness, diagnostics, operator guide | Re-run all automated suites in the **live** environment, no secret exposure, clean install/restart/smoke test, no regression in voice/desktop workflows. User performs one consolidated manual test matrix at the end; failures are triaged and retested before any "ready" claim. |

## Test policy

Each stage has unit tests, integration tests with controlled fixtures, and a
final real-world acceptance case. Tests must assert **observed outcome**, not
merely an API call or text marker. Timing tests report hardware, provider,
network, sample size, and percentiles; they do not promise universal speed.
Cloud and phone tests require available credentials/devices and may cost money.
No credentials, document bodies, or spoken transcripts enter durable audit
logs. Deployment makes exact-file backups and preserves user changes.

## Final manual session (after implementation)

1. Speak the fixed English/Roman Urdu prompt set and check transcript, accent,
   interruption, silence recovery, and provider fallback.
2. Launch and close an installed app; request a nonexistent app; control two
   windows; browse the **Windows default** browser; verify each visible result.
3. Index an explicitly chosen PDF, cite a late passage, run a current research
   dossier, then create and visually inspect PDF, DOCX, and PPTX outputs.
4. Complete a multi-step workflow twice, inspect its learned hint, disable it,
   and confirm the next run still re-observes and verifies every action.
5. Pair the intended Android phone, launch one installed package, then prove
   wrong-serial/offline handling. Only test smart-home hardware if an adapter
   and actual device have been commissioned.

Until those cases pass, report each stage as implemented, automated-tested,
real-world-tested, or blocked, never as a blanket 100%.
