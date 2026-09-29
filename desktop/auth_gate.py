"""Pre-launch, single-account Supabase sign-in for the desktop cockpit.

This is an app launch gate, not an OS boundary: someone with local code/process
access can start individual JARVIS services directly. No token or password is
written to disk or passed to child processes.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable


ALLOWED_EMAIL = "muhammedayaan213@gmail.com"


class AuthError(Exception):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise AuthError("Unexpected authentication redirect")


def _open_no_redirect(request, timeout: float):
    return urllib.request.build_opener(_NoRedirect).open(request, timeout=timeout)


class SupabaseLogin:
    def __init__(self, url: str, key: str, *, opener: Callable = _open_no_redirect):
        parsed = urllib.parse.urlsplit(url.strip().rstrip("/"))
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
                parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
            raise AuthError("Supabase URL must be an HTTPS project origin")
        if not key or len(key) > 4096 or "\n" in key or "\r" in key:
            raise AuthError("Supabase publishable/anon key is missing or invalid")
        self.origin = f"https://{parsed.netloc}"
        self.key = key
        self.opener = opener

    def _json_request(self, path: str, *, token: str = "", body: dict | None = None) -> dict:
        headers = {"apikey": self.key, "Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(self.origin + path, data=data, headers=headers,
                                         method="POST" if body is not None else "GET")
        with self.opener(request, timeout=12) as response:
            if urllib.parse.urlsplit(response.geturl()).netloc != urllib.parse.urlsplit(self.origin).netloc:
                raise AuthError("Unexpected authentication redirect")
            raw = response.read(32769)
            if len(raw) > 32768:
                raise AuthError("Authentication response was too large")
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise AuthError("Invalid authentication response")
        return result

    def sign_in(self, password: str) -> bool:
        if not isinstance(password, str) or not 1 <= len(password) <= 1024:
            raise AuthError("Enter your password")
        try:
            session = self._json_request("/auth/v1/token?grant_type=password",
                                         body={"email": ALLOWED_EMAIL, "password": password})
            token = session.get("access_token")
            if not isinstance(token, str) or not token:
                raise AuthError("Sign-in did not return a session")
            user = self._json_request("/auth/v1/user", token=token)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError,
                ValueError, json.JSONDecodeError) as exc:
            raise AuthError("Sign-in failed. Check your password and connection") from exc
        if (not isinstance(user.get("id"), str) or
                str(user.get("email") or "").casefold() != ALLOWED_EMAIL):
            raise AuthError("This account is not allowed to open JARVIS")
        return True


AUTH_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>JARVIS sign in</title>
<style>
:root{color-scheme:dark;font-family:'Segoe UI',Arial,sans-serif}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;
background:#020705;color:#e8f0e9}.gate{width:min(390px,calc(100vw - 48px));
padding:32px;border:1px solid #21412d;border-radius:12px;background:#09140f}
.mark{width:40px;height:40px;display:grid;place-items:center;border:1px solid #3ddc84;
color:#3ddc84;border-radius:7px;font-size:23px;font-weight:700}
h1{font-size:24px;line-height:1.2;font-weight:500;margin:24px 0 8px}
p{color:#87a292;margin:0 0 25px;line-height:1.5}label{display:block;margin:14px 0 7px;font-size:13px}
.email{color:#b4c9bb;background:#0c1b13;border:1px solid #21412d;border-radius:6px;
padding:11px 12px;overflow-wrap:anywhere}input{width:100%;background:#102018;color:#e8f0e9;
border:1px solid #2a4d36;border-radius:6px;padding:11px 12px;font:inherit}
button{width:100%;margin-top:22px;border:0;border-radius:6px;background:#3ddc84;
color:#061009;font:700 14px 'Segoe UI',Arial,sans-serif;padding:12px;cursor:pointer}
button:disabled{opacity:.55;cursor:wait}input:focus-visible,button:focus-visible{outline:2px solid #3ddc84;outline-offset:2px}
#error{min-height:21px;color:#ff6875;font-size:12px;margin:12px 0 0}
</style></head><body><main class="gate"><div class="mark" aria-hidden="true">J</div>
<h1>Open your JARVIS</h1><p>Sign in to start the desktop session.</p>
<form id="login"><label>Email</label><div class="email">muhammedayaan213@gmail.com</div>
<label for="password">Password</label><input id="password" type="password" required
autocomplete="current-password" maxlength="1024"><button id="submit" type="submit">Sign in</button>
<div id="error" role="alert" aria-live="polite"></div></form></main><script>
document.getElementById('login').addEventListener('submit',async event=>{
 event.preventDefault();const button=document.getElementById('submit');
 const input=document.getElementById('password');const error=document.getElementById('error');
 button.disabled=true;error.textContent='';
 try{const result=await window.pywebview.api.sign_in(input.value);input.value='';
  if(!result.ok){error.textContent=result.error||'Sign-in failed';button.disabled=false;input.focus();}}
 catch(_){input.value='';error.textContent='Sign-in unavailable. Try again.';button.disabled=false;}
});
</script></body></html>"""


class LoginBridge:
    def __init__(self, login: SupabaseLogin):
        self.login = login
        self.authorized = False
        self.window = None
        self._last_attempt = 0.0

    def sign_in(self, password: str) -> dict:
        now = time.monotonic()
        if now - self._last_attempt < 1.0:
            return {"ok": False, "error": "Wait a moment before trying again"}
        self._last_attempt = now
        try:
            self.login.sign_in(password)
        except AuthError as exc:
            return {"ok": False, "error": str(exc)}
        self.authorized = True
        if self.window is not None:
            self.window.destroy()
        return {"ok": True}


def main() -> int:
    try:
        login = SupabaseLogin(os.environ.get("SUPABASE_URL", ""),
                              os.environ.get("SUPABASE_ANON_KEY", ""))
    except AuthError:
        print("JARVIS login is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.")
        return 2
    import webview

    bridge = LoginBridge(login)
    bridge.window = webview.create_window("JARVIS — Sign in", html=AUTH_HTML,
                                           js_api=bridge, width=480, height=570,
                                           min_size=(420, 520),
                                           background_color="#020705")
    webview.start(gui="edgechromium", private_mode=True)
    return 0 if bridge.authorized else 2


if __name__ == "__main__":
    raise SystemExit(main())
