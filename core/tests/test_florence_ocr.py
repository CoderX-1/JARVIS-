import json
import os
import base64
import sys
import threading
import types
import unittest
import urllib.request
from http.server import HTTPServer
from unittest.mock import Mock, patch

from florence_client import FlorenceClient
from florence_worker import Handler


class _Image:
    def convert(self, mode):
        assert mode == "RGB"
        return self

    def save(self, target, _format, **_kwargs):
        target.write(b"fixture-image")


class _Response:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return self.body


class FlorenceOcrClientTests(unittest.TestCase):
    def test_disabled_ocr_never_connects(self):
        with patch.dict(os.environ, {"JARVIS_FLORENCE_ENABLED": "0"}):
            client = FlorenceClient()
        client._opener = Mock()
        self.assertIsNone(client.ocr(_Image()))
        client._opener.open.assert_not_called()

    def test_local_ocr_request_and_bounded_result(self):
        with patch.dict(os.environ, {"JARVIS_FLORENCE_ENABLED": "1"}):
            client = FlorenceClient()
        client._opener = Mock()
        client._opener.open.return_value = _Response({"text": "Recognized page text"})
        self.assertEqual(client.ocr(_Image()), "Recognized page text")
        request = client._opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8795/ocr")
        self.assertLess(len(request.data), 14_000_000)
        self.assertNotIn(b"OPENAI_API_KEY", request.data)

    def test_failed_ocr_is_not_empty_success(self):
        with patch.dict(os.environ, {"JARVIS_FLORENCE_ENABLED": "1"}):
            client = FlorenceClient()
        client._opener = Mock()
        client._opener.open.side_effect = OSError("worker offline")
        self.assertIsNone(client.ocr(_Image()))


class FlorenceOcrRouteTests(unittest.TestCase):
    def test_ocr_route_dispatches_without_query(self):
        class _DecodedImage:
            width = 16
            height = 16

            def convert(self, mode):
                self.assert_mode = mode
                return self

        image_module = types.SimpleNamespace(Image=types.SimpleNamespace(open=lambda _data: _DecodedImage()))
        grounder = Mock()
        grounder.ocr.return_value = ("JARVIS OCR TEST", 0.25)
        server = HTTPServer(("127.0.0.1", 0), Handler)
        server.grounder = grounder
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            payload = json.dumps({"image": base64.b64encode(b"fixture").decode("ascii")}).encode("utf-8")
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/ocr",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with patch.dict(sys.modules, {"PIL": image_module}):
                with urllib.request.urlopen(request, timeout=3) as response:
                    answer = json.load(response)
            self.assertEqual(answer["text"], "JARVIS OCR TEST")
            grounder.ocr.assert_called_once()
            grounder.ground.assert_not_called()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
