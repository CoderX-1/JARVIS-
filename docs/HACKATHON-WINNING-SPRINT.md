# JARVIS Hackathon Sprint - September 26, 2026

Status: active five-day sprint. The official event link, theme, rules, judging
rubric, submission cutoff, and demo time are still required.

## Product claim

> JARVIS is a voice-first, evidence-driven computer agent. It can perceive a
> live Windows desktop, research current information with sources, discover and
> operate installed applications, verify outcomes, and recover instead of
> blindly repeating failed actions.

Do not claim ASI, unrestricted autonomy, full browser DOM control, mobile
control, smart-home control, or robotics in the September 26 demo unless that
capability has passed its live acceptance test.

## Why this can score

The differentiator is not another chatbot or a list of scripted commands. The
demo proves one complete loop:

1. Hear one natural-language outcome.
2. Research fresh information and expose its sources.
3. Inspect the actual desktop state.
4. Discover and control the required application dynamically.
5. Verify the postcondition after each action.
6. Re-observe and recover when the UI changes.
7. Report evidence, uncertainty, and failures truthfully.

## September 26 winning scope

### Must ship

- stable PTT, listening/thinking/speaking states, and provider failover;
- Fish Audio primary voice with truthful provider reporting;
- dedicated read-only live web research with source URLs;
- dynamic installed-app discovery and verified app/window control;
- Vision-Control Engine, UI State Graph, self-healing selectors, watchdog,
  duplicate guard, and interaction guard;
- one rehearsed end-to-end mission combining research and desktop action;
- one deliberately changed UI state followed by visible recovery;
- evidence-backed completion report with no false-success claim;
- reproducible automated tests and a one-command demo readiness check;
- polished README/demo script plus a short prerecorded fallback video.

### Ship only if the must-have demo is already reliable

- lightweight Mission Control page showing current step and evidence;
- persistent single-mission task ledger;
- phone-readable local status page;
- simulated provider outage and OpenAI-to-Gemini brain failover;
- exportable evidence bundle.

### After the hackathon

- native phone control and accessibility agents;
- Home Assistant, Matter, MQTT, wearables, and room nodes;
- ROS 2 robotics and vehicle telemetry;
- multi-agent delegation and long-running proactive missions;
- broad connector catalog and controlled skill learning.

These remain in `JARVIS-OMEGA-ROADMAP.md`; they are not deleted from the
product direction.

## Three-minute demo

### 0:00-0:20 - Problem

"Most assistants either answer questions or replay brittle automation. JARVIS
connects perception, current research, action, verification, and recovery."

### 0:20-0:35 - One spoken goal

Use a theme-specific mission when the rubric is known. Until then:

> "Jarvis, research the latest official information about [demo topic], open
> Notepad, write a five-line cited briefing, and tell me only after you verify
> that it is on screen."

### 0:35-1:15 - Current research

JARVIS searches the live web, produces a concise answer, and keeps the returned
source titles and URLs. The judge sees that the answer is not stale model
memory.

### 1:15-2:05 - Desktop execution

JARVIS discovers Notepad rather than relying on a fixed path, opens it, verifies
the window, types Unicode text without using the clipboard, and checks visible
content/state.

### 2:05-2:35 - Recovery moment

Move, cover, rename, or change the expected control before the rehearsed step.
JARVIS rejects stale evidence, re-observes through UI Automation/OCR/vision, and
uses an alternate selector. Do not improvise the failure injection on demo day.

### 2:35-3:00 - Proof and vision

Show sources, action audit, postconditions, and the absence of a false success.
Close with: "Today this verified contract controls Windows; the same contract
can extend to phones, homes, and robots without changing what 'done' means."

## Five-day work order

### September 21 - Freeze truth and add current research

- deploy and live-test the `research_web` tool;
- run all core regressions;
- create a timestamped backup;
- restart JARVIS and complete a voice-triggered manual test;
- capture baseline ports, providers, and known limitations.

### September 22 - Integrate the winning mission

- create the bounded research-to-desktop workflow;
- attach sources and postcondition evidence;
- add a reset command and deterministic demo data;
- test the exact workflow ten times.

### September 23 - Recovery and evidence

- rehearse one moved/changed UI target;
- expose the selector fallback and UI State Graph evidence;
- ensure interruption, timeout, modal, and duplicate handling remain truthful;
- produce a compact evidence bundle.

### September 24 - Presentation layer

- add only the minimum Mission Control/status UI that strengthens the story;
- write the README, architecture graphic, judge FAQ, and exact spoken script;
- record the fallback video on the presentation machine.

### September 25 - Feature freeze

- no new features except severity-one demo blockers;
- run 20 consecutive rehearsals and log results;
- verify microphone, speaker, network, keys, ports, and display scaling;
- test reset, offline explanation, provider failure, and fallback video;
- make a recoverable tagged/archived release.

### September 26 - Demo day

- use the frozen build and known machine state;
- warm voice and API providers before judging;
- do not update packages, Windows, models, or credentials;
- run the rehearsed mission, not an untested feature tour.

## Release gates

The build is stage-ready only when:

- the exact demo succeeds at least 19 of 20 consecutive times;
- no run reports success without a postcondition;
- critical spoken nouns/actions are correct in at least 9 of 10 runs;
- web research returns at least one inspectable source or clearly fails;
- the recovery injection succeeds at least 9 of 10 times;
- secrets never appear in logs, screenshots, speech, or evidence;
- the whole demo fits the official time limit;
- reset and fallback video both work on the presentation laptop.

## Information still needed

Send the official hackathon page or rule document. It will be used to map the
demo, README, and every pitch sentence directly to the scoring rubric. Until
then, reliability and demonstrable technical depth take priority over adding
more integrations.
