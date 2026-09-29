# Android integration status and final acceptance

JARVIS currently has a bounded ADB app-launch adapter. It is not a background
phone agent and does not grant arbitrary control. ADB itself is powerful, so
only pair a phone you own and trust, and revoke debugging authorization when
you no longer want the PC to access it.

## Current contract

- `android_status` checks one exact serial configured by the user.
- `find_android_apps` searches installed package identifiers on that device.
- `launch_android_app` checks that the exact package is installed, sends one
  launcher intent, and checks the foreground activity afterward. A sent intent
  without observed foreground state is **unverified**.
- Raw ADB shell, APK installation, uninstall, force-stop, phone typing,
  message sending, and permission changes are not exposed to the model.
- Results and arguments are redacted in the durable Mark II action audit.

The adapter has passed offline/fake-ADB tests. This PC currently has no ADB
Platform-Tools detected; there has been no connected Android-phone test.

## One-time setup, when ready for the final manual session

1. Install Google's [official SDK Platform-Tools for Windows](https://developer.android.com/tools/releases/platform-tools)
   after reviewing its terms. Do not download an unofficial `adb.exe`.
2. On the Android phone, enable Developer options and USB debugging; connect
   by cable, or follow Google's [wireless debugging procedure](https://developer.android.com/tools/adb)
   if the phone supports it. Approve the PC's debugging fingerprint on the phone.
3. Run `adb devices -l` locally to identify the exact connected serial. A
   state of `device` means ADB transport is connected, not that Android is
   fully ready. Do not guess a serial when multiple devices are present.
4. Add `JARVIS_ANDROID_SERIAL=<exact serial>` to JARVIS's private `.env`. If
   `adb.exe` is not on PATH or in the standard Android SDK location, also add
   `JARVIS_ADB_PATH=<absolute path to adb.exe>`. Do not paste pairing codes,
   device serials, or the private `.env` into chat or a public repo.

## Final manual tests (deferred until the user's end-of-build session)

1. Ask JARVIS for Android status. Expect connected only for the exact serial.
2. Ask it to find an installed package, then open that exact package. On the
   phone, verify it is foreground and the response says verified.
3. Ask it to open an uninstalled package. Expect a no-launch explanation.
4. Disconnect or revoke debugging, then try again. Expect offline/unauthorized
   and no action sent.
5. Connect two devices without changing the configured serial. Confirm JARVIS
   still addresses only the chosen device.
6. Check the action audit for redaction and inspect the phone for unintended
   installs, messages, or other side effects.

## Next architecture

For reliable everyday phone control, a least-privilege Android companion app
with per-capability consent and an authenticated local transport is preferable
to leaving ADB enabled. It needs a separate Android project, signing,
permission design, pairing UI, and real-device tests. None of those are
complete; the current ADB bridge is an explicit, limited first adapter.
