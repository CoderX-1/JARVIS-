# JARVIS workspace

This repository is a source snapshot of a local JARVIS installation. Private
API keys, memory, downloaded models, runtime signals/logs, and backups are not
published. Those must be configured or restored locally after cloning.

The running desktop installation is normally `C:\Projects\JARVIS`; open that
folder when you want to run JARVIS. This GitHub repository is the development
source. `fullstack-agent-main` is the older installer/workspace that originally
supplied the provider-neutral `core/agent.py`; the historical name in a few
internal files does not mean there is a second assistant to start.

- "core/" - provider-neutral agent, Mark II tools, installer overlays, tests
- "components/backtalk/" - push-to-talk microphone and speech
- "components/ai-visualizer/" - face on port 8790
- "components/barehands/" - hands board on port 8794
- "config/" - portable configuration examples; copy each `*.example.json`
  to its matching `.json` filename and replace placeholder paths and voice IDs
- "memory/" - private long-term notes and memory (not in GitHub)
- "models/" - downloaded local model cache (not in GitHub)
- "runtime/logs/" and "runtime/signals/" - generated runtime data
- ".env" - private API keys; never share or commit it

## Restore a local installation

Copy `core/.env.example` to `.env` and set your provider keys locally. Copy
each `config/*.example.json` to the same name without `.example`, then set
your own paths, voice reference, and microphone. Install dependencies and
download required models using the guides in `core/` and each `components/`
folder. Restore your own memory vault separately. These private and generated
files are deliberately absent from GitHub.

After restoring your `.env`, configuration, memory, and model dependencies,
start with `START-JARVIS-DESKTOP.bat`. Hold HOME while speaking, then release it.
The sample voice configuration uses push-to-talk, Gemini transcription,
Fish Audio speech with Gemini fallback, and a local transcription standby.

The private teacher-PC release is built locally with `BUILD-PRIVATE-RELEASE.ps1`
and is never committed. Its passwordless option embeds the unlock secret inside
the ZIP: convenient for installation, but anyone with that ZIP can recover the
bundled API keys. Installer unlock and the optional Supabase account sign-in
are separate. On a new PC the installer still needs Windows, internet access,
Python/dependency downloads, and a compatible PPTX viewer such as PowerPoint.

Source provenance and the licenses of vendored components are documented in
`THIRD-PARTY.md`.
