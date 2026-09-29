# JARVIS: what it can do, and what that actually means

This describes the installed tool registry and current acceptance boundaries
on 29 September 2026. It is not a promise that every tool works on an
unconfigured laptop. Open the native app's **Abilities** tab to see the exact
registered names; open **Activity** to see what a particular action actually
verified. The same request can be spoken with HOME or typed in the app.

## How one request travels through JARVIS

1. Hold HOME and speak, or type in the app. For speech, Gemini transcription
   tries first and local Whisper can be a fallback. The recognized words
   appear in the conversation so you can catch a mishearing.
2. The AI provider (OpenAI with Gemini fallback, according to local config)
   interprets the request. The model does not directly control Windows; it
   selects from a bounded set of registered tools with structured arguments.
3. The selected tool checks current state and exact targets. Windows control
   uses UI Automation, process/window identity, and where needed screenshot
   OCR or offline Florence. Browser control checks the live URL and page.
4. After an action, a verification contract looks for an observed result.
   **Verified**, **observed**, **delivered**, **failed**, and **unknown** are
   different outcomes; a generated sentence alone is not success.
5. Fish Audio normally speaks the reply, with Gemini configured as a cloud
   fallback. The Board face reflects listening/thinking/speaking status; it
   is not a second brain. Local services communicate through `127.0.0.1`
   internally, but JARVIS is opened as a native WebView2 app, not a browser
   page for the user.

## What you can ask today

| Area | Example request | What JARVIS attempts | Important limit |
| --- | --- | --- | --- |
| Normal conversation | “Explain this idea simply.” | AI answer in the same app/voice session | Model can be wrong; ask for sources on factual claims |
| PC health | “Check CPU, RAM, disk and battery.” | Reads current Windows measurements | Fan and temperature may be unavailable |
| Apps | “Find and open Calculator.” | Searches installed apps, opens an exact match, checks for its window | Nonexistent or ambiguous app should be reported, not guessed |
| Windows | “Focus/minimize/restore/close Notepad.” | Targets a particular visible window/handle | Close is graceful; unsaved prompts must not be bypassed |
| Typing | “Type this sentence into Notepad.” | Targets one app and types Unicode text | Does not type into an unverified target or a password field |
| UI controls | “Find the Save button in this window.” | Inspects accessibility tree; may use OCR/visual target ranking | A stale/ambiguous control needs fresh observation |
| Screen vision | “Read visible text in this app.” | Captures one target window, redacts password fields, runs local OCR | Not full omniscience; screenshots may miss hidden content |
| Default-browser tasks | “Open this website and tell me its title.” | Uses Windows default browser in an isolated profile and verifies URL/title | This intentionally opens a browser; the JARVIS app itself stays native |
| YouTube | “Play a normal YouTube video about …” | Searches, starts video, checks playback state | Site changes/network/ads can block it |
| Web research | “Research this topic and cite sources.” | Bounded public search and original-page checks | Citation/quote support is not complete factual proof |
| Supplied pages | “Inspect this public URL and check this quote.” | Direct read and exact text check | Private/localhost URLs are refused; paywalls/JS pages may fail |
| PDF | “Create a cited professional PDF brief from these URLs.” | Reads 1–3 safe pages, synthesizes with Gemini, generates source-linked PDF | Inspect real claims and page layout before sharing |
| PPTX | “Create an editable presentation from these URLs.” | Generates source-attributed editable text slides | Package tested; visual PowerPoint acceptance pending |
| Existing files | “Index this PDF, then find the section about …” | Indexes only an explicitly named TXT/MD/PDF/DOCX/PPTX and returns page/slide locators | No automatic drive scan; scanned PDF OCR is bounded |
| Forget index | “Forget the indexed copy of this document.” | Removes JARVIS index entries | Original document remains on disk |
| Projects | “List/register/check/start this project.” | Tracks exact path/approved dev commands/git/localhost health | No arbitrary unregistered command execution by design |
| Generated app | “List or launch the saved app.” | Checks the stored build/version/hash before launch | Generated Python is not protected by an OS sandbox |
| Workflow hints | “What workflows did you learn?” | Shows privacy-minimal patterns from verified repetitions | Not autonomous self-training or blind macro replay |
| Android | “Check phone status; find/open exact package.” | Uses official ADB on one configured serial, verifies foreground app | ADB and phone are not paired here; no full phone control |
| Spatial | Click ring/orbs in the Spatial tab | Mouse-driven spatial interface without a camera | Hand tracking needs camera and real gesture testing |

## Built-in reliability and limits

- **Verification engine:** tool-specific postconditions stop JARVIS from
  calling every click “done.” **Watchdog** bounds stuck operations.
  **Duplicate guard** resists repeated accidental execution. **Interaction
  guard** watches for modal blockers and human input. **UI State Graph**
  remembers privacy-safe patterns, but fresh state is still checked.
- **Vision-Control:** accessibility selectors first, OCR/image templates and
  local Florence as bounded fallbacks. This is useful for dynamic UIs, not
  guaranteed control of every app or secure/UAC desktop.
- **Research cost:** direct supplied-URL PDF/PPTX briefs use safe page reads
  and one Gemini synthesis request; topic briefs add one Brave discovery
  query. Other `research_web`/`research_dossier` routes use OpenAI web search
  and may cost more. Asking the AI alone without sources is faster but less
  dependable for current facts.
- **Privacy:** local document indexing is opt-in; normal vision observations
  are not saved as screenshots unless explicitly requested. The app must
  never display API keys. Some cloud speech/research tasks send content to
  configured providers; do not demonstrate private data in class.

## Not ready or not honestly proven yet

Dedicated polished DOCX export; fully visually accepted PPTX; Pakistani Urdu
accent judged good by the user; real camera hand gestures; real paired Android
and smart-home devices; Gmail OAuth/read/draft/send/notification; fully live
Supabase sign-in; clean-machine signed Windows installer; universal control
of any app/site; human-level or “ASI” intelligence. These are engineering
targets, not current capabilities. See `CLASS-DEMO-AND-FULL-TEST-BUNDLE.md`
for the final PASS/FAIL tests.
