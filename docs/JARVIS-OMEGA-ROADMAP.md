# JARVIS Omega — universal autonomous intelligence roadmap

Status date: 2026-09-21

This is the master roadmap beyond Windows Control Ultra. It defines a
measurable path toward movie-style JARVIS behavior across computers, phones,
homes, sensors, wearables and robots. It does **not** claim that current models
are artificial superintelligence. The target is an ASI-inspired system whose
capabilities are demonstrated by repeatable evidence rather than a label.

Development remains gate-based: one bounded component is implemented,
automatically tested, tested against a native or simulated target, manually
accepted, and backed up before the next component begins.

## North-star behavior

The finished system should be able to receive an outcome such as:

> Prepare my workday, check the house, move my active task to my phone when I
> leave the desk, monitor it, and tell me only if intervention is needed.

JARVIS should then:

1. establish the intended result and constraints;
2. inspect available devices, applications and services;
3. build a dependency-aware plan;
4. select the best provider, agent and device for each step;
5. execute reversible steps without micromanagement;
6. verify real state after every action;
7. recover, re-plan or roll back when reality differs from expectation;
8. preserve useful context and discard secrets;
9. remain interruptible from voice, phone, desktop or an emergency stop;
10. report completion only with an evidence bundle.

This is goal-driven behavior, not a large list of hard-coded voice commands.

## Reality boundary

“Movie JARVIS” is the interaction target. “ASI” is not a valid completion
claim unless a future system passes independently defined general-intelligence
evaluations. Current limitations remain real:

- model reasoning can be wrong;
- devices expose different capabilities and permissions;
- iOS and Android deliberately restrict background control;
- cloud providers can fail, throttle or change;
- physical actuators can create consequences software undo cannot reverse;
- no model receives universal, permanent or invisible authority.

The system can still become highly autonomous inside explicit mission scopes.

## Reference architecture

```text
 Voice / text / vision / sensors / schedules / device events
                         |
                  Presence Gateway
                         |
             Cognitive Kernel + World Model
        +----------------+----------------+
        |                |                |
   Goal Graph       Memory Fabric     Policy Engine
        |                |                |
        +---------- Orchestrator ----------+
                         |
     Planner -> Specialists -> Executor -> Verifier
                         |
                  Universal Action Bus
       +-----------+-----------+-----------+---------+
       |           |           |           |         |
    Desktop      Mobile     Home/IoT     Cloud    Robotics
       |           |           |           |         |
   UI/OS state  App state   Device twins  APIs    ROS 2 state
       +-----------+-----------+-----------+---------+
                         |
            Evidence / Audit / Recovery Journal
```

### Core contracts

Every device and action uses the same typed contracts:

- **Device descriptor:** stable identity, owner, location, capabilities,
  connection health, software/firmware version and trust level.
- **Digital twin:** last observed state, freshness, desired state, uncertainty
  and active operations.
- **Action envelope:** goal ID, action ID, target, parameters, preconditions,
  expiry, idempotency key, risk class, expected result and rollback strategy.
- **Result envelope:** accepted/rejected/unknown, timestamps, observations,
  changed fields, confidence, evidence references and retry advice.
- **Event envelope:** source, sequence, causal goal, severity, privacy class,
  time-to-live and acknowledgement state.

No adapter is allowed to return bare “success.” It must return observed state
or an honest “unknown.”

## Autonomy ladder

Autonomy is assigned per domain and device rather than through one global
permission switch.

| Level | Name | Behavior |
|---|---|---|
| A0 | Observe | Read state, explain and recommend only |
| A1 | Assist | Prepare a plan or draft; user initiates execution |
| A2 | Act | Execute one reversible action and verify it |
| A3 | Mission | Execute a bounded multi-step goal, re-plan and roll back |
| A4 | Steward | Monitor a declared domain and act on approved policies |
| A5 | Proactive | Initiate low-risk missions from events and learned routines |

A5 is not unlimited control. Safety-critical, destructive, financial,
identity, medical, lock/security and high-energy physical actions retain
device interlocks and explicit policies regardless of conversational mode.

## Capability domains

The universal action bus must eventually cover:

- Windows, Linux and macOS application/OS control;
- Android and iPhone companion applications;
- browsers, email, calendars, files, messaging and collaboration systems;
- smart lights, climate, media, plugs, blinds, vacuums and supported appliances;
- cameras, microphones, occupancy, environmental and energy sensors;
- watches, earbuds and health/wellness summaries with privacy isolation;
- ESP32/Raspberry Pi and custom MQTT devices;
- local servers, NAS, containers and development environments;
- telepresence, mobile robots and manipulators through ROS 2;
- vehicle telemetry and manufacturer-approved remote functions;
- room-to-room presence and seamless conversation handoff.

## Delivery program

### Gate 0 — Current Mark II foundation

Existing foundation:

- Vision-Control Engine;
- UI State Graph;
- self-healing selectors;
- action verification and watchdog;
- smart typing foundation;
- OpenAI brain with Gemini fallback;
- Gemini speech recognition;
- Fish Audio cloud voice with Gemini TTS fallback;
- local semantic vision through Florence;
- Windows application and project-control tools.

Remaining Mark II Windows work continues under
`WINDOWS-CONTROL-ULTRA-ROADMAP.md`; it becomes one adapter beneath Omega,
not the entire JARVIS architecture.

Exit gate: current Fish voice manual test is accepted and the existing Mark II
regression suite remains green.

### Gate 1 — Cognitive Kernel: persistent Goal and Task Ledger

Build first because every later device depends on it.

- persistent goals, missions, tasks, dependencies and subgoals;
- states: proposed, ready, running, waiting, verifying, succeeded, failed,
  blocked, cancelled and rolled-back;
- atomic journal and crash recovery;
- leases so two agents cannot execute the same task;
- deadlines, budgets, retry limits and cancellation propagation;
- evidence requirements attached before execution;
- human-readable live mission summary;
- no model-generated executable code inside the ledger.

Automated gate:

- schema/property tests;
- concurrent claim tests;
- power-loss and corrupted-tail recovery;
- duplicate action suppression;
- dependency/cycle detection;
- secret-redaction tests.

Manual gate: create a three-step mission, interrupt JARVIS, restart it and
verify it resumes only the unfinished step.

### Gate 2 — Planner, Executor, Verifier and Recovery loop

- outcome-first hierarchical planner;
- tool/device capability discovery before planning;
- independent verifier that cannot mark its own action successful;
- precondition and postcondition checks;
- alternative-method recovery;
- compensating actions and rollback journals;
- bounded critic/evaluator loop;
- uncertainty and ambiguity escalation;
- progress speech without blocking execution.

Manual gate: give an outcome whose UI changes mid-run; JARVIS must re-observe,
re-plan and finish without repeating an uncertain click.

### Gate 3 — Memory Fabric and Personal World Model

- short working memory for the current mission;
- episodic memory for completed events and decisions;
- semantic memory for stable facts and preferences;
- procedural memory for verified reusable skills;
- temporal world model for people, places, devices, projects and commitments;
- provenance, confidence, expiry and contradiction tracking;
- user-visible inspect/edit/forget controls;
- sensitive-memory classes that never enter model history;
- retrieval evaluation to prevent irrelevant-memory contamination.

Manual gate: demonstrate remembering a non-sensitive preference, correcting it,
and proving the obsolete value is no longer retrieved.

### Gate 4 — Specialist Agent Mesh

- one orchestrator with bounded specialists for planning, Windows, mobile,
  home, research, coding, memory and verification;
- typed mailbox messages rather than free-form agent chatter;
- shared ledger/blackboard with ownership and hop limits;
- provider/cost/latency governor;
- evaluator disagreement handling;
- deadlock, livelock and runaway-token containment;
- per-agent capability tokens and isolated secret access.

Manual gate: a cross-domain mission must show which specialist owned each
step, while the orchestrator retains one coherent conversation.

### Gate 5 — Proactive Event and Routine Engine

- schedules, timers, geofences and device-state triggers;
- compound conditions and temporal windows;
- debouncing, cooldowns and duplicate-event suppression;
- quiet hours and interruption policy;
- simulation/dry-run view for every routine;
- learned routine proposals, never silent enrollment;
- anomaly detection based on explicit baselines;
- ongoing mission supervision and resumable background work.

Manual gate: simulate repeated arrival events and prove only one routine runs.

### Gate 6 — Universal Desktop completion

- finish Gates 5–10 of Windows Control Ultra;
- add Linux AT-SPI and compositor adapters;
- add macOS Accessibility/App Intents adapters;
- cross-device clipboard with secret classification;
- multi-monitor, virtual desktop and remote-session awareness;
- transactional file operations and recycle/restore;
- native app adapters plus universal vision fallback;
- browser DOM adapter with visual verification;
- process health, crash recovery and resource governance.

Manual gate: execute the same semantic workflow on two desktop platforms with
platform-specific actions but identical result contracts.

### Gate 7 — Android JARVIS Companion

Build a dedicated Android app; do not depend on fragile ADB scripting for the
production path.

- mutual device enrollment and certificate identity;
- encrypted WebSocket/event channel;
- microphone/PTT and Fish voice playback;
- notification stream with app/category filters;
- current foreground app and accessibility-tree perception;
- accessibility actions and gestures where the user enables the service;
- MediaProjection-based screen context only during an OS-approved session;
- share-sheet, intents, deep links, media controls and files selected by user;
- location/geofence, battery, network and device-presence events;
- offline queued missions with expiry and replay protection;
- visible status, pause and emergency-disconnect controls.

Android Enterprise Management is a separate optional adapter for enrolled
enterprise/dedicated devices, not a shortcut to unrestricted personal-phone
control.

Manual gate: start a mission on PC, continue it on Android, verify the target
app state, then revoke the phone and prove subsequent commands fail closed.

### Gate 8 — iPhone, iPad and Apple Watch bridge

iOS cannot provide Android-style universal background UI control. Use supported
system surfaces instead:

- native companion app with secure event channel;
- App Intents, App Shortcuts, Siri, Spotlight and widgets;
- Shortcuts automations for opted-in cross-app workflows;
- notifications and actionable intents;
- share sheet, files selected by user, camera/microphone sessions;
- Watch complications, Action button intents and concise mission status;
- HomeKit/Matter integration through approved frameworks;
- handoff/deep links into apps that expose them.

Manual gate: invoke a JARVIS App Intent from iPhone/Watch, execute a bounded
mission and verify its result on the PC ledger.

### Gate 9 — Home, Matter and IoT fabric

Use Home Assistant as the initial integration hub because it exposes device
state, service calls and event streaming. Add direct adapters only where they
provide a verified benefit.

- Home Assistant REST for state/service operations;
- Home Assistant WebSocket for live events and subscriptions;
- Matter 1.6 devices through a supported controller/hub;
- MQTT 5 for custom sensors and actuators;
- Zigbee/Thread/Z-Wave through existing trusted coordinators;
- automatic capability discovery and normalized digital twins;
- scenes, occupancy, energy, climate and media orchestration;
- local-first operation during internet loss;
- command expiry, idempotency and actual-state verification;
- device health, battery, firmware and stale-state detection.

Physical policy classes:

- P0 informational sensors;
- P1 reversible comfort/media devices;
- P2 appliances and unattended energy loads;
- P3 doors, alarms, cameras and security boundaries;
- P4 heat, motion, water, machinery and other safety-critical actuation.

Higher classes require progressively stronger interlocks, independent sensors
and fail-safe defaults. Conversational auto-approve does not override them.

Manual gate: run the complete suite first against virtual devices, then one
real low-risk light or media device, including network-loss recovery.

### Gate 10 — Edge Nodes and Ambient Presence

- signed ESP32/Raspberry Pi device runtime;
- room microphone/speaker nodes with local wake detection;
- camera nodes with privacy shutters and visible capture state;
- occupancy, air quality, temperature, motion and energy sensors;
- local inference for wake/VAD and privacy-sensitive filtering;
- room-to-room voice handoff based on authenticated presence;
- clock synchronization and event ordering;
- over-the-air updates with signature and rollback;
- no raw continuous audio/video retention by default.

Manual gate: move between two rooms during one conversation; exactly one node
must speak and context must transfer without duplicate execution.

### Gate 11 — Wearables and personal context

- watch/earbud quick commands, haptics and status summaries;
- phone-mediated presence and activity context;
- opt-in wellness summaries separated from normal memory;
- privacy-preserving on-device filtering;
- lost-device revoke and key rotation;
- emergency-contact features only through explicit, tested workflows.

Health data informs summaries; it does not produce medical diagnosis or
autonomous treatment.

### Gate 12 — Robotics and physical embodiment

Start in simulation, then low-energy hardware.

- ROS 2 topics for continuous state;
- services for short synchronous operations;
- actions for long-running operations with feedback/cancellation;
- SROS2 security enclaves and signed permissions;
- digital twin, localization, mapping and sensor fusion;
- motion planning with collision constraints;
- independent hardware emergency stop and watchdog;
- speed/force/workspace limits and human-presence zones;
- simulation, replay and hardware-in-the-loop tests;
- dual-channel verification for physical outcomes;
- no general actuator command generated directly by an LLM.

Manual gates progress from simulator, to an indicator, to a low-energy mobile
base, never directly to high-force manipulation.

### Gate 13 — Vehicle and mobility integration

- read-only telemetry first: location, charge/fuel, range and maintenance;
- route and charging planning;
- manufacturer-approved remote climate/lock APIs where available;
- trip handoff between phone, vehicle and home;
- strict rate limits, geofences, audit and credential isolation;
- no driving, steering, braking or safety-system control.

Any future motion-control work belongs to certified automotive systems, not a
general assistant model.

### Gate 14 — Cloud and organization connectors

- email, calendar, files, documents, tasks, chat and development platforms;
- connector-specific scopes and separate identities;
- draft/review/send state distinction;
- external side-effect ledger;
- deduplication and idempotent webhook processing;
- data-loss prevention and recipient/tenant boundary checks;
- local encrypted cache with deletion propagation;
- offline queue with expiry, ordering and conflict resolution.

Manual gate: run a cross-service workflow entirely in test accounts and prove
that retries cannot send duplicates.

### Gate 15 — Real-time multimodal “Astra-style” presence

- duplex voice with interruption and echo control;
- continuously refreshed visual scene graph while a session is active;
- deictic grounding: “this,” “that one,” “the window on the left”;
- temporal references: “before that,” “when it finishes,” “the earlier error”;
- multiple camera/device viewpoints with freshness and source labels;
- adaptive bandwidth and local privacy filtering;
- predictive prefetch that never performs an action before intent is known;
- sub-second acknowledgement separate from deeper reasoning;
- conversation and mission execution remain independently cancellable.

Manual gate: interrupt an in-progress explanation, refer to a newly appeared
object without naming it, and confirm JARVIS grounds and acts on the fresh
state rather than the previous frame.

### Gate 16 — Controlled skill learning and self-improvement

- learn semantic workflows only from verified demonstrations;
- generalize parameters, never coordinates or secrets;
- generate a regression test before promoting a learned skill;
- shadow/dry-run, canary and rollback stages;
- signed versioned skill registry;
- offline evaluation datasets and failure replay;
- compare candidate strategies on success, latency, cost and reversibility;
- model/prompt changes require measurable improvement without safety loss;
- no unrestricted self-modification or silent deployment.

Manual gate: teach one workflow, change the UI, and prove the semantic skill
adapts while a deliberately ambiguous variant refuses or requests resolution.

### Gate 17 — Reliability, privacy and fleet operations

- local certificate authority, mutual TLS and automatic rotation;
- per-device and per-agent capability grants;
- encrypted secrets vault and hardware-backed keys where available;
- tamper-evident audit chain;
- health dashboard, traces, latency/cost metrics and distributed correlation;
- network partition handling and eventual reconciliation;
- backup/restore, disaster recovery and clean device revocation;
- chaos tests for provider, network, power and device failures;
- privacy modes, retention schedules and export/delete tooling;
- red-team suite for prompt injection, spoofed devices and unsafe plans.

Exit gate: a multi-day synthetic household/office evaluation completes with no
duplicate high-impact action, no leaked secret, no false completion and proven
recovery from injected failures.

## Cross-cutting intelligence systems

These evolve across multiple gates rather than being built once:

### Provider and compute governor

- fast/cheap model for routing and ordinary voice;
- deep model only for genuinely difficult planning;
- OpenAI primary with Gemini failover;
- local models for privacy-sensitive perception and offline degradation;
- per-mission token, money, time, energy and network budgets;
- circuit breakers, health scores and truthful degradation.

### Identity and presence

- distinguish person, device and session identities;
- never infer identity from voice alone for sensitive actions;
- track room/device presence with confidence and expiry;
- prevent two endpoints from answering or executing the same turn;
- support guests and shared spaces without exposing private memory.

### Evidence and observability

- every action emits structured traces and postcondition evidence;
- dashboards show goal graph, active agent, device state and blockers;
- privacy-safe screenshots/sensor snapshots when necessary;
- replay tools recreate decisions without secrets;
- latency is separated into hearing, reasoning, action, verification and speech.

### Safety and recovery

- emergency stop works without cloud or model access;
- expired commands never execute after reconnection;
- stale sensor state cannot satisfy a postcondition;
- physical actions use independent watchdogs and hardware limits;
- irreversible actions cannot be made reversible by wording;
- uncertainty produces a safe stop or bounded alternative, never invented state.

## Test pyramid for every adapter

1. schema and deterministic unit tests;
2. contract tests with fake device/service;
3. recorded failure replay;
4. simulator or digital-twin integration;
5. network loss, duplicate, delay and reordering injection;
6. native smoke against a disposable target;
7. hardware-in-the-loop for physical devices;
8. user manual acceptance;
9. canary period with rollback ready;
10. regression added before progression.

## Immediate execution order

Only the next component is active at a time:

1. record Fish voice manual acceptance;
2. Gate 1 Component 1: Task Ledger schema and atomic persistence;
3. Component 2: dependency graph and task claims;
4. Component 3: crash recovery and idempotency;
5. Component 4: evidence requirements and mission status;
6. Gate 1 full automated/native/manual acceptance;
7. begin Gate 2 planner/executor/verifier loop;
8. continue existing Windows Gate 5 work as an adapter track;
9. start Android companion only after the universal action contracts stabilize;
10. start Home Assistant/MQTT only after device identity and digital twins exist.

This ordering prevents separate desktop, phone and home implementations from
becoming incompatible automation silos.

## Definition of “movie-like enough”

The project may describe itself as movie-style JARVIS only after it can:

- sustain a multi-hour, cross-device mission;
- understand live voice and visual references;
- discover unfamiliar tools and device capabilities;
- plan, execute, verify, recover and resume;
- maintain coherent personal and environmental context;
- act proactively in explicitly governed low-risk domains;
- hand a mission between desktop, phone, room and edge nodes;
- explain what it believes, what it does not know and why it acted;
- demonstrate zero false-success reports in the acceptance evaluation;
- remain interruptible and recoverable at every stage.

It still must not claim consciousness, omniscience or real ASI.

## Standards and primary integration references

- Home Assistant WebSocket API:
  https://developers.home-assistant.io/docs/api/websocket/
- Home Assistant REST API:
  https://developers.home-assistant.io/docs/api/rest/
- Matter 1.6 release:
  https://csa-iot.org/newsroom/matter-1-6-enables-more-intuitive-setup-multi-ecosystem-experiences-and-context-driven-control/
- MQTT standard overview and specification:
  https://mqtt.org/ and https://mqtt.org/mqtt-specification/
- Android Accessibility Service:
  https://developer.android.com/guide/topics/ui/accessibility/service
- Android MediaProjection:
  https://developer.android.com/media/grow/media-projection
- Android notification listener:
  https://developer.android.com/reference/android/service/notification/NotificationListenerService
- Android Management API, enterprise scope:
  https://developers.google.com/android/management/introduction
- Apple App Intents:
  https://developer.apple.com/documentation/appintents
- Apple Matter support:
  https://developer.apple.com/apple-home/matter/
- ROS 2 topics, services and actions:
  https://docs.ros.org/en/ros2_documentation/jazzy/How-To-Guides/Topics-Services-Actions.html
- ROS 2 security keystore and enclaves:
  https://docs.ros.org/en/ros2_documentation/jazzy/Tutorials/Advanced/Security/The-Keystore.html
