import io
import json
import unittest
import urllib.error
import urllib.request

from auth_gate import ALLOWED_EMAIL, AUTH_HTML, AuthError, LoginBridge, SupabaseLogin


class Response:
    def __init__(self, url, value):
        self.url = url
        self.raw = io.BytesIO(json.dumps(value).encode())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.raw.read(limit)


class AuthGateTests(unittest.TestCase):
    def test_two_step_sign_in_checks_server_identity(self):
        requests = []

        def opener(request, timeout):
            requests.append(request)
            self.assertEqual(timeout, 12)
            if len(requests) == 1:
                self.assertEqual(request.full_url,
                                 "https://demo.supabase.co/auth/v1/token?grant_type=password")
                self.assertEqual(json.loads(request.data),
                                 {"email": ALLOWED_EMAIL, "password": "correct"})
                return Response(request.full_url, {"access_token": "session-token"})
            self.assertEqual(request.get_header("Authorization"), "Bearer session-token")
            return Response(request.full_url, {"id": "user-id", "email": ALLOWED_EMAIL})

        login = SupabaseLogin("https://demo.supabase.co", "public-key", opener=opener)
        self.assertTrue(login.sign_in("correct"))
        self.assertEqual(len(requests), 2)

    def test_wrong_account_and_failed_password_never_authorize(self):
        def wrong_user(request, timeout):
            if request.data is not None:
                return Response(request.full_url, {"access_token": "token"})
            return Response(request.full_url, {"id": "user-id", "email": "other@example.com"})

        login = SupabaseLogin("https://demo.supabase.co", "public-key", opener=wrong_user)
        with self.assertRaisesRegex(AuthError, "not allowed"):
            login.sign_in("password")

        def bad_password(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 400, "invalid", {}, None)

        bridge = LoginBridge(SupabaseLogin("https://demo.supabase.co", "public-key",
                                          opener=bad_password))
        self.assertFalse(bridge.sign_in("wrong")["ok"])
        self.assertFalse(bridge.authorized)

    def test_config_redirect_and_ui_are_fail_closed(self):
        for url in ("", "http://demo.supabase.co", "https://user@demo.supabase.co",
                    "https://demo.supabase.co/other"):
            with self.assertRaises(AuthError):
                SupabaseLogin(url, "public-key")

        def redirect(request, timeout):
            return Response("https://untrusted.example/", {"access_token": "token"})

        login = SupabaseLogin("https://demo.supabase.co", "public-key", opener=redirect)
        with self.assertRaisesRegex(AuthError, "redirect"):
            login.sign_in("password")
        self.assertNotIn("sign up", AUTH_HTML.casefold())
        self.assertNotIn("href=", AUTH_HTML.casefold())
        self.assertIn(ALLOWED_EMAIL, AUTH_HTML)


if __name__ == "__main__":
    unittest.main()
