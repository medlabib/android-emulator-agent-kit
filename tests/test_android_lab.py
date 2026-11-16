import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from tools.android_lab import adb, encode_input_text, package_id, run, verify, wait_boot

class AndroidLabTests(unittest.TestCase):
    def test_text_spaces_are_encoded(self):
        self.assertEqual(encode_input_text("Hello world 42"), "Hello%sworld%s42")
    def test_text_rejects_unsafe_and_unicode(self):
        for value in ("x; reboot", "a'b", "مرحبا", "", "a\\nbreak"):
            with self.subTest(value=value), self.assertRaises(ValueError): encode_input_text(value)
    def test_text_is_bounded(self):
        with self.assertRaises(ValueError): encode_input_text("a"*501)
    def test_package_validation(self):
        self.assertEqual(package_id("com.example.app"),"com.example.app")
        for value in ("com..bad","com.example;id","../app","app"):
            with self.subTest(value=value), self.assertRaises(ValueError): package_id(value)
    @patch("tools.android_lab.subprocess.run")
    def test_adb_requires_and_passes_explicit_serial(self,mock_run):
        mock_run.return_value=Mock(returncode=0,stdout="ok",stderr="")
        self.assertEqual(adb("emulator-5554","shell","id"),"ok")
        self.assertEqual(mock_run.call_args.args[0][:3],["adb","-s","emulator-5554"])
    def test_missing_serial_rejected(self):
        with self.assertRaises(ValueError): adb("","shell","id")
    @patch("tools.android_lab.subprocess.run")
    def test_timeout_is_actionable(self,mock_run):
        mock_run.side_effect=subprocess.TimeoutExpired(["adb","devices"],1)
        with self.assertRaisesRegex(RuntimeError,"timed out"): run(["adb","devices"],timeout=1)

    @patch("tools.android_lab.subprocess.run", side_effect=FileNotFoundError)
    def test_missing_adb_is_actionable(self, _mock_run):
        with self.assertRaisesRegex(RuntimeError, "Command not found: adb"):
            run(["adb", "devices"])

    @patch("tools.android_lab.adb")
    def test_verify_requires_boot_completion(self, mock_adb):
        mock_adb.side_effect = [
            "package:com.android.vending\npackage:com.google.android.gms",
            "14", "34", "0",
        ]
        with self.assertRaises(SystemExit) as error:
            verify(SimpleNamespace(serial="emulator-5554"))
        self.assertEqual(error.exception.code, 2)

    def test_wait_boot_rejects_non_positive_timeout(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            wait_boot(SimpleNamespace(serial="emulator-5554", timeout=0))

if __name__=="__main__": unittest.main()
