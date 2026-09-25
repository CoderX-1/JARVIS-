# Mark-LIV Inspiration Audit for JARVIS Omega

Date: 2026-09-21

Source reviewed: `FatihMakes/Mark-LIV` on GitHub. The source project is
CC BY-NC 4.0. JARVIS will use architectural inspiration only; no source file,
function, prompt, or asset is copied.

## What the logs proved we need

- Saying "open browser" was treated as a literal application name instead of
  resolving the system/default browser.
- Native browser/window control could open and focus Brave, but YouTube's
  repeated text and dynamic layout defeated first-video selection.
- The agent spent 20-47 seconds in visual retries and still could not prove
  playback.
- Web research returned current information correctly, but a request for the
  latest official OpenAI announcement used third-party sources because the
  user did not constrain the search to official domains.
- Fish handled every logged utterance, yet voice identity could vary because
  no reference voice was configured.

## Ideas worth adapting

### 1. Dedicated browser execution layer

Mark-LIV separates ordinary OS browser launch from interactive DOM automation.
JARVIS should take that principle further with its own Browser Control Engine:

- resolve "browser" to the Windows default browser;
- use a dedicated JARVIS browser profile for automation instead of attaching to
  a locked personal profile;
- DOM roles, labels, text, URLs, titles, media state, and accessibility tree as
  primary evidence;
- existing Windows UI Automation/OCR/Florence as fallback, not first choice;
- precondition and postcondition for every mutation;
- YouTube playback is verified from the media element state and URL, never from
  the fact that a thumbnail was clicked;
- downloads, logins, purchases, messages, and form submission remain separate
  policy-gated actions.

### 2. Runtime self-knowledge

Generate capability and limitation text from the live tool registry and runtime
health. This prevents claims about missing tools and removes stale hard-coded
capability lists.

### 3. Self-describing components

Move future tools toward validated descriptors plus handlers, but retain
JARVIS's stronger verification contracts, watchdog, duplicate guard, and audit
requirements. A module that cannot declare its postcondition must not become a
mutating tool.

### 4. Undo receipts

For reversible mutations, store an explicit inverse operation and the evidence
needed to prove rollback. Undo is not added to actions such as sending a
message, publishing, deleting remote data, or making a purchase.

### 5. Instant acknowledgement and evidence UI

Long research or vision work should immediately acknowledge the goal, then show
the current phase and evidence without pretending completion. This fits the
hackathon Mission Control rather than adding a cosmetic-only avatar first.

### 6. Echo discrimination

Mark-LIV compares assistant output audio with microphone input. JARVIS can later
combine output-loopback correlation with its existing PTT/barge-in state so it
does not transcribe its own voice while still allowing real interruption.

## What not to adopt

- Do not scrape the first YouTube `videoId`, open it, and report "Playing"
  without observing playback.
- Do not expose or automate a user's normal browser profile by default; profile
  locks, sessions, cookies, and extensions increase reliability and privacy
  risk.
- Do not store provider secrets in ordinary JSON configuration.
- Do not auto-load arbitrary Python plugins without schema validation,
  permission classification, crash isolation, and verification contracts.
- Do not claim zero subscriptions, total autonomy, ASI, or capabilities that
  are not proven by the current runtime.

## JARVIS advantages to preserve

- Verification Engine outcome states instead of generic "Done" strings;
- Action Watchdog and stuck-operation containment;
- Duplicate Action Guard and blind-repeat prevention;
- Interaction Guard for modals and human input;
- Vision-Control Engine with UI Automation, OCR, templates, and Florence;
- UI State Graph and fresh-state verification;
- OpenAI/Gemini brain failover and Fish/Gemini TTS failover;
- privacy-redacted audit trail.

## Delivery order before September 26

1. Lock Fish to one reference voice and low-variation synthesis settings.
2. Browser Control Engine Phase 1: default-browser resolution, dedicated Brave
   automation profile, navigation/read/click/type/media-state tools, and tests.
3. Verified YouTube search-and-play mission using DOM media state.
4. Runtime capability/limitation manifest generated from live tools.
5. Minimal Mission Control evidence panel and instant progress acknowledgement.

Each component must pass automated tests, a native smoke test, and a user manual
gate before the next component begins.
