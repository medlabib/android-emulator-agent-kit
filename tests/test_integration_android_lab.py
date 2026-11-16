import json
import os
import shutil
import subprocess
import unittest


ADB = os.environ.get("ANDROID_ADB", "adb")
SERIAL = os.environ.get("ANDROID_SERIAL", "")
ENABLED = os.environ.get("ANDROID_LAB_INTEGRATION") == "1"
AVAILABLE = shutil.which(ADB) is not None and bool(SERIAL)


@unittest.skipUnless(
    ENABLED and AVAILABLE,
    "Set ANDROID_LAB_INTEGRATION=1, ANDROID_SERIAL, and provide adb to run emulator tests.",
)
class AndroidLabIntegrationTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            ["python", "tools/android_lab.py", *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_selected_device_is_boot_ready(self):
        result = self.run_cli("verify", "--serial", SERIAL, "--json")
        self.assertIn(result.returncode, (0, 2), result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["serial"], SERIAL)
        self.assertEqual(payload["boot_completed"], "1")

    def test_selected_device_can_dump_ui(self):
        result = self.run_cli("ui-dump", "--serial", SERIAL, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("<hierarchy", json.loads(result.stdout)["xml"])
