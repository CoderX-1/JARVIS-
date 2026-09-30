"""Device-selection transport tests; no microphone or camera hardware needed."""

import json
import queue
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from spatial_direct import DirectSpatial

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "components" / "backtalk"))
from backtalk.desktop_bridge import DesktopBridge


class DeviceBridgeTests(unittest.TestCase):
    def test_list_select_and_reject_unknown_microphone(self):
        selected = []
        listed = lambda: {"selected": selected[-1] if selected else "",
                          "inputs": [{"id": "USB microphone [WASAPI]",
                                      "name": "USB microphone", "host": "WASAPI"}]}
        with tempfile.TemporaryDirectory() as tmp:
            bridge = DesktopBridge(queue.Queue(), tmp, port=0,
                                   list_mics=listed,
                                   select_mic=lambda name: selected.append(name) or True)
            bridge.start()
            try:
                base = f"http://127.0.0.1:{bridge.port}"
                with self.assertRaises(urllib.error.HTTPError) as missing_token:
                    urllib.request.urlopen(base + "/devices")
                self.assertEqual(missing_token.exception.code, 403)
                headers = {"X-Jarvis-Token": bridge.token}
                with urllib.request.urlopen(urllib.request.Request(base + "/devices", headers=headers)) as reply:
                    self.assertEqual(json.load(reply)["inputs"][0]["id"], "USB microphone [WASAPI]")
                def choose(name):
                    request = urllib.request.Request(base + "/mic",
                        data=json.dumps({"device": name}).encode(), method="POST", headers=headers)
                    return urllib.request.urlopen(request)
                with self.assertRaises(urllib.error.HTTPError) as unknown:
                    choose("Unplugged")
                self.assertEqual(unknown.exception.code, 409)
                with choose("USB microphone [WASAPI]") as reply:
                    self.assertEqual(json.load(reply)["selected"], "USB microphone [WASAPI]")
                self.assertEqual(selected, ["USB microphone [WASAPI]"])
            finally:
                bridge.stop()

    def test_spatial_adapter_forwards_selected_camera(self):
        root = Path(__file__).resolve().parent.parent
        js = DirectSpatial(root).js.decode("utf-8")
        self.assertIn('Q.set("cam", Q.get("spatialCam"))', js)
        self.assertIn('Q.set("role", "preview")', js)


if __name__ == "__main__":
    unittest.main()
