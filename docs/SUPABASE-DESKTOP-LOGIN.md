# Single-account Supabase login for JARVIS desktop

Status: gate code is staged in source and live install, but disabled until the
owner configures the project and passes a real login test. It gates the
`RUN-JARVIS.ps1 -Desktop` launcher **before** any JARVIS service is started.
It is not an OS security boundary: a person with access to local code or the
Windows account could start services directly. Never describe it as remote
device protection or complete encryption of local files.

## One-time Supabase dashboard setup

1. In your own Supabase project, go to Authentication → Users. Create/invite
   exactly `muhammedayaan213@gmail.com`, set a strong unique password, and
   complete email confirmation if your project requires it.
2. In Authentication settings, disable **Allow new users to sign up**. The
   JARVIS UI has no signup form, but the dashboard setting is also required
   so the public API cannot create another account.
3. Find the project URL and its publishable/anon key. Do **not** use a
   service-role/secret key in a desktop application. Never paste the password
   or key into chat, a demo slide, logs, or Git.
4. Add these three lines to the private `C:\Projects\JARVIS\.env` file:

   ```text
   SUPABASE_URL=https://YOUR-PROJECT.supabase.co
   SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_OR_ANON_KEY
   JARVIS_AUTH_REQUIRED=1
   ```

   The email is fixed in the login gate; there is no email chooser or signup.

## Acceptance before the class demo

1. Close JARVIS fully. Launch from the interactive Windows desktop:
   `powershell -NoProfile -ExecutionPolicy Bypass -File C:\Projects\JARVIS\RUN-JARVIS.ps1 -Desktop`.
2. Cancel the sign-in window. The launcher must exit without starting the
   microphone, brain, Board, Spatial, or vision services.
3. Launch again, enter a wrong password. The app must show a generic failure
   and remain at sign-in; no services start. Do not repeatedly brute-force.
4. Launch again, enter the correct password. The native Board cockpit must
   open and show Brain connected after service startup.
5. Disconnect internet and launch once. It must fail closed; restore network
   afterwards. The password is never stored for offline bypass.
6. Verify that only the allowed Supabase user succeeds. If anything fails,
   set `JARVIS_AUTH_REQUIRED=0` for the demo and report login as unaccepted;
   do not claim it was tested.

The launcher only supplies Supabase public configuration to the gate process.
Model API keys are withheld until login completes, and no Supabase access
token/password is saved. The project still needs an eventual clean-PC
installer test, first-run configuration flow, and access controls for any
future remote service. This gate protects the standard desktop launcher, not
all possible ways to execute local code.
