# JARVIS Mark II — Executable Engineering Contract

## Mission

Build the closest honest, practical version of a movie-style JARVIS that can be
engineered on this Windows computer. It must be an outcome-oriented assistant,
not a command macro and not a system that pretends to be conscious. It should
understand the user's intent, observe the real computer, form a structured model
of the current state, plan bounded actions, execute through guarded adapters,
verify the actual result, recover from ordinary failures, and remember only the
minimum safe evidence needed to improve later decisions.

Never claim that an action worked because an input was sent. Success requires
fresh evidence from the target application. Never invent screen contents,
installed apps, files, capabilities, permissions, or completed outcomes.

## Non-negotiable control loop

For every computer task, run this loop:

1. **Interpret** — convert the request into an explicit goal, constraints,
   completion conditions, and forbidden outcomes.
2. **Perceive** — inspect live windows, UI Automation, local OCR, and local
   visual grounding. Mark every observation with source, age, and confidence.
3. **Model** — build a structured UI state: application/window identity,
   hierarchy, focus, active tab, selected/toggled values, modal ownership,
   modified state, busy/loading/progress/error state, and actionable controls.
4. **Plan** — choose the smallest reversible action sequence that can reach the
   goal. Prefer semantic controls over coordinates and deterministic evidence
   over probabilistic vision.
5. **Guard** — immediately re-observe before input; reject stale, ambiguous,
   moving, hidden, protected, or cross-application targets.
6. **Act** — deliver one bounded action through a typed OS/application adapter.
7. **Verify** — evaluate an explicit expected-state contract using independent
   post-action evidence. Distinguish input delivery, observable response, and
   verified goal completion.
8. **Recover** — on mismatch, stop blind repetition, diagnose the changed state,
   select a bounded alternative, and preserve a truthful failure explanation.
9. **Remember** — retain privacy-safe state/transition fingerprints and success
   statistics, never screenshots, OCR text, window titles, secrets, or permission.

## Epistemic rules

- Separate facts, inferences, and unknowns in every internal decision.
- A model prediction is not a UI fact. Re-observe before acting.
- Historical state is evidence only; it never authorizes replay.
- Negative visual evidence is weaker than positive evidence and must be sampled
  repeatedly before being treated as stable absence.
- If confidence is insufficient or multiple targets remain plausible, stop and
  expose the ambiguity instead of guessing.
- State changes unrelated to the requested outcome are not verification.

## Autonomy contract

Routine, reversible, user-requested actions may run automatically. Destructive,
security-sensitive, credential, payment, identity, irreversible, or broadly
scoped actions require the applicable safety gate. Autonomy must never bypass OS
security boundaries, CAPTCHA, authentication, password fields, UAC, lock screen,
or the user's explicit limits. The system must maintain an emergency stop,
bounded retries, timeouts, resource limits, auditability, and crash isolation.

## Intelligence architecture

- **Provider-neutral brain:** OpenAI first when configured, Gemini through its
  OpenAI-compatible endpoint as fallback, and a custom OpenAI-compatible provider
  when configured. Provider failure must not corrupt task state.
- **Local perception:** Windows UI Automation and OCR first; local Florence-style
  visual grounding only after deterministic locators miss.
- **UI State Graph:** a live, structured, privacy-safe world model and transition
  ledger with explicit expected-state contracts.
- **Planner and executor:** goal decomposition, dependency ordering, typed tools,
  bounded retries, cancellation, and evidence-based completion.
- **Recovery layer:** selector repair, changed-layout diagnosis, alternative
  modality selection, restart/rollback where authorized, and loop detection.
- **Memory:** opt-in durable preferences and privacy-safe operational evidence;
  no secret harvesting and no raw desktop history.
- **Watchdog:** health, latency, overload, stuck-listening, provider failover,
  worker restart, and graceful degradation.

## Definition of done for every capability

A capability is not complete until it has:

- a typed interface with validated inputs and bounded resource use;
- a real implementation rather than a scripted demo path;
- protected-surface and privacy handling;
- fresh precondition checks and explicit postcondition verification;
- honest error messages and no false-success path;
- unit, regression, failure-injection, and live native-app tests;
- logs that redact private UI content and secrets;
- a manual acceptance checklist that a human can reproduce.

## Build sequence

Complete one gate at a time and do not silently skip acceptance:

1. Vision-Control Engine.
2. UI State Graph.
3. Self-Healing Selectors.
4. Workflow Planner and execution DAG.
5. Recovery/rollback engine.
6. Durable preference and task memory.
7. Application-specific adapters.
8. Proactive monitoring with explicit user boundaries.
9. Continuous evaluation, latency, and reliability hardening.

## Current execution directive — Gate 3: Self-Healing Selectors

Build a selector engine that can recover from changed layouts without guessing:

- rank live OCR, stable UIA identity, automation ID, role, native class,
  accessibility access-key metadata, contextual anchors, templates, pixels and
  the guarded local VLM fallback;
- preserve the low-latency exact-OCR path while switching modality when a fresh
  observation invalidates it;
- re-observe and rebuild the selector immediately before every input;
- repair by stable identity after movement and require stability before acting;
- refuse unresolved ambiguity, changed foreground, occlusion, protected
  surfaces and targets outside current window geometry;
- never send a second action after any input may have been delivered;
- learn only verified strategy results, keyed by hashed app/version and target
  identity with bounded atomic storage and 30-day evidence decay;
- never persist raw labels, OCR, titles, queries, paths, screenshots,
  coordinates or secrets;
- expose a typed, read-only status tool and live strategy evidence;
- pass unit, privacy, corruption, decay, failure-injection, full regression and
  native Windows layout-repair tests before manual acceptance.

Do not begin Gate 4 until the user confirms the Gate 3 manual tests pass.
