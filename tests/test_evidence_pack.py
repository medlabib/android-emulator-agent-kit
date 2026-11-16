import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.evidence_pack import build_bundle, local_report_links


class EvidencePackTests(unittest.TestCase):
    def test_extracts_local_links_and_ignores_remote_links(self):
        report = (
            "![screen](screens/home.png)\n"
            "[details](logs/logcat.txt)\n"
            "[external](https://example.com/report)\n"
            "[anchor](#results)\n"
        )
        self.assertEqual(
            local_report_links(report),
            ["screens/home.png", "logs/logcat.txt"],
        )

    def test_builds_bundle_with_linked_files_metadata_and_checksums(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "screens").mkdir()
            screenshot = root / "screens" / "home.png"
            screenshot.write_bytes(b"fake-png")
            report = root / "journey.md"
            report.write_text(
                "# Journey: Login\n![Home](screens/home.png)\n"
                "[remote](https://example.com)\n",
                encoding="utf-8",
            )
            metadata = root / "metadata.json"
            metadata.write_text(
                json.dumps({"app": {"package": "org.example.demo"}, "device": {"api": 35}}),
                encoding="utf-8",
            )
            extra = root / "logcat.txt"
            extra.write_text("ActivityManager: test", encoding="utf-8")
            archive_path = root / "out" / "evidence.zip"

            manifest = build_bundle(report, archive_path, metadata, [extra])

            self.assertEqual(manifest["schema_version"], "1.0")
            self.assertEqual(manifest["metadata"]["app"]["package"], "org.example.demo")
            self.assertEqual(manifest["warnings"], [])
            self.assertEqual(len(manifest["artifacts"]), 3)
            screenshot_entry = next(item for item in manifest["artifacts"] if item["path"] == "screens/home.png")
            self.assertEqual(screenshot_entry["sha256"], hashlib.sha256(b"fake-png").hexdigest())

            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"journey.md", "manifest.json", "screens/home.png", "attachments/logcat.txt"},
                )
                packaged = json.loads(archive.read("manifest.json"))
                self.assertEqual(packaged["artifacts"], manifest["artifacts"])
                self.assertEqual(archive.read("screens/home.png"), b"fake-png")

    def test_does_not_package_path_traversal_or_missing_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "secret.txt"
            outside.write_text("private", encoding="utf-8")
            report_dir = root / "reports"
            report_dir.mkdir()
            report = report_dir / "journey.md"
            report.write_text(
                "[outside](../secret.txt)\n[missing](not-there.png)\n",
                encoding="utf-8",
            )
            archive_path = root / "evidence.zip"

            manifest = build_bundle(report, archive_path)

            self.assertEqual(manifest["artifacts"][0]["path"], "journey.md")
            self.assertEqual(len(manifest["warnings"]), 2)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(set(archive.namelist()), {"journey.md", "manifest.json"})
                self.assertNotIn(b"private", archive.read("journey.md"))

    def test_metadata_must_be_a_json_object(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "journey.md"
            report.write_text("# Journey", encoding="utf-8")
            metadata = root / "metadata.json"
            metadata.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must contain an object"):
                build_bundle(report, root / "evidence.zip", metadata)

    def test_rejects_non_zip_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "journey.md"
            report.write_text("# Journey", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, ".zip"):
                build_bundle(report, root / "evidence.tar")


if __name__ == "__main__":
    unittest.main()
