# Private Windows release (owner hand-off)

This release is for a **trusted Windows 11 x64 laptop**, not public download.
The ZIP contains JARVIS source and local models in plaintext; `.env` and the
three local configuration files are protected with AES-256-GCM and a
600,000-iteration PBKDF2-SHA256 key derivation. The passphrase is entered in
the local terminal, never placed in the command line, repository, or chat.

For a passwordless class-demo package, run `./BUILD-PRIVATE-RELEASE.ps1
-PasswordlessInstall`. This embeds the unlock passphrase in the ZIP so install
does not prompt. It is not meaningful protection for the API keys: anyone who
receives the ZIP can recover them. Never publish that ZIP or push it to GitHub.
The default build remains encrypted with a separately delivered passphrase.

Encryption protects the ZIP in transit. Once installed, API keys must be
available to JARVIS and therefore the laptop owner/administrator can retrieve
them. If that laptop is not trusted, do not install this release. Use separate
restricted API keys, usage limits, and revoke them afterward.

## On the owner's PC

1. Complete desktop login and full manual tests on the live JARVIS first.
2. Ensure Python 3.12 and `cryptography` are installed on the builder PC.
3. In a PowerShell terminal, run `./BUILD-PRIVATE-RELEASE.ps1` from this source
   checkout. It reads `.env`, local configs, and models from `C:\Projects\JARVIS`
   by default. It generates one strong install passphrase locally; no keys are
   typed or printed.
4. The ZIP and a separate password text file appear in `.jarvis-private/`.
   Both are gitignored. Transfer **only the ZIP** to the laptop; keep the
   password file separately and type its contents at install time. Never push
   or publicly host the ZIP.

The builder refuses an existing ZIP, missing models/config, symlinks in the
model tree, oversized payloads, and unexpected source paths. The archive has
per-file SHA-256 manifest entries bound to the encrypted payload. Decryption
and integrity are checked before any installation folder is created. The
installer scripts themselves are not code-signed: obtain the ZIP through a
trusted channel and do not run scripts from an untrusted or modified copy.

## On the trusted recipient laptop

1. Requirements: Windows 11 x64, internet during setup, Windows Package Manager
   (`winget`), and enough free disk space for the ZIP, extracted sources/models,
   Python wheels, and local models (allow at least 8 GB). The installer uses winget
   to add Python 3.12 x64, FFmpeg, and WebView2 when they are missing.
   Do not use a public/shared/classroom PC with the owner's production keys.
2. Copy the private ZIP by a private channel. Extract the whole ZIP in Windows
   Explorer. Double-click `Install-JARVIS.bat` in the extracted folder. The
   original ZIP is found automatically if it is beside the extracted folder;
   otherwise give its full path when prompted. Enter the passphrase locally.
3. Installer creates `%LOCALAPPDATA%\Programs\JARVIS` without overwriting an
   existing directory, rebuilds the voice, desktop, and Florence Python
   environments, installs browser support, and runs dependency import checks.
   It needs network access. If a package install fails, the folder is left for
   diagnosis; **do not treat that as a passed installation**.
4. Open `START-JARVIS-DESKTOP.bat` in the installed folder. Sign in using the
   configured account. Test microphone push-to-talk, spoken response, app
   opening, browser actions, PDF, PPTX, Files shelf, and Recycle Bin on that
   actual laptop. Camera/Android need their respective hardware and setup.

The installer does not configure a microphone for another laptop and cannot
guarantee performance on unknown hardware. A school-managed PC may block
winget, downloaded packages, microphone access, or WebView2; in that case the
admin must allow them before this release can be accepted.
The ZIP is a testable release candidate until a clean-laptop manual test passes.

## Local validation

From `tools`: `python -m unittest -q test_private_release.py`. From `core`:
`python -m unittest discover -s tests -q`. Wrong-password, tamper, checksum,
path safety, and no-overwrite behavior are covered. These do not substitute
for an actual install and opening the generated PPTX in PowerPoint.
