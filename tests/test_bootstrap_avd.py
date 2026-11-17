import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "bootstrap-avd.sh"


@unittest.skipUnless(shutil.which("bash"), "bash is required for the provisioning-script test")
class BootstrapAvdTests(unittest.TestCase):
    def test_uses_custom_avd_home_and_updates_camera_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sdk = root / "sdk"
            bin_dir = sdk / "cmdline-tools" / "latest" / "bin"
            bin_dir.mkdir(parents=True)
            home = root / "home"
            home.mkdir()
            avd_home = root / "custom-avds"
            avd_home.mkdir()

            sdkmanager = bin_dir / "sdkmanager"
            sdkmanager.write_text(
                "#!/usr/bin/env bash\n"
                'if [[ "${1:-}" == "--licenses" ]]; then IFS= read -r _ || true; exit 0; fi\n'
                "exit 0\n",
                encoding="utf-8",
            )
            sdkmanager.chmod(0o755)

            avdmanager = bin_dir / "avdmanager"
            avdmanager.write_text(
                "#!/usr/bin/env bash\n"
                'if [[ "${1:-}" == "list" ]]; then echo "No AVDs found"; exit 0; fi\n'
                'if [[ "${1:-}" == "create" ]]; then\n'
                "  shift 2\n"
                "  while [[ $# -gt 0 ]]; do\n"
                '    if [[ "$1" == "--name" ]]; then name="$2"; shift 2; else shift; fi\n'
                "  done\n"
                '  mkdir -p "$ANDROID_AVD_HOME/$name.avd"\n'
                '  printf "hw.camera.back=emulated\\nhw.camera.front=emulated\\n" > "$ANDROID_AVD_HOME/$name.avd/config.ini"\n'
                "  exit 0\n"
                "fi\n"
                "exit 1\n",
                encoding="utf-8",
            )
            avdmanager.chmod(0o755)

            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "ANDROID_SDK_ROOT": str(sdk),
                "ANDROID_AVD_HOME": str(avd_home),
            })
            result = subprocess.run(
                ["bash", str(SCRIPT), "35", "Agent_Test_AVD"],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            config = avd_home / "Agent_Test_AVD.avd" / "config.ini"
            self.assertTrue(config.is_file())
            self.assertIn("hw.camera.back=webcam0", config.read_text(encoding="utf-8"))
            self.assertIn("hw.camera.front=webcam0", config.read_text(encoding="utf-8"))
            self.assertIn("Created/verified AVD: Agent_Test_AVD", result.stdout)


if __name__ == "__main__":
    unittest.main()
