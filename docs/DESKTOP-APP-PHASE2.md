# JARVIS desktop cockpit — phase 2

The desktop cockpit now has five views while keeping one agent/voice session:
Live core, Action history, Abilities, Created files, and Android readiness. The chat pane
remains available in every view. Browser and spatial workspaces still open in
the system default browser; they are not embedded yet.

## Evidence, not imagined status

- Action history reads a bounded tail of JARVIS's existing audit and shows
  only timestamp, tool name, and the verification-engine status. It does not
  render audit arguments, results, or evidence text, even from old records.
  `verified`, `observed`, and `delivered` remain distinct.
- The latest durable task plan is summarized by its recorded step states.
  No UI click marks a task complete.
- Abilities reads the installed Mark II registry as static syntax, without
  importing or executing the core module. It currently lists 66 registered
  tools, including 27 action tools. These are discoverable descriptions, not
  a claim that every integration is configured or live-tested.
- Created files lists only PDF/DOCX/PPTX files immediately inside
  `JARVIS/output/reports` and saved App Foundry catalog entries. It ignores
  symlinks/out-of-scope files. Opening a report requires an explicit click;
  generated apps are not launched from the shelf and still require the
  agent's integrity re-check.
- Android view checks only whether Platform-Tools and an exact serial are
  configured. It does not call a phone, claim one is connected, or bypass the
  existing exact-serial verification tool. The "Ask JARVIS" button prepares a
  message rather than sending a hidden action.

## Automated and visual checks

- 5 observability/privacy tests and 3 desktop-bridge tests pass.
- Local mock UI smoke verified typed-turn flow and rendered the new views.
- Screenshots reviewed at 1320×820 and minimum 1030×650. A real layout bug
  in Tk pack propagation was found and corrected before deployment.
- Existing 134 live-core and 28 root tests are rerun for release regression.

## Remaining work

The cockpit is not a complete packaged product. In-window browser/spatial
embedding, artifact previews, real Android pairing, provider-backed voice
acceptance, DOCX/PPTX authoring, and a signed installer remain separate
milestones. They require their own implementation and real-device tests;
the presence of a UI view is not evidence that those capabilities are ready.
