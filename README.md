# 🤖 Android Emulator Agent Kit

**Experimental evidence packaging for Android CLI agent-driven tests.**

This project is evolving to complement [Google's official Android CLI](https://developer.android.com/tools/agents/android-cli), not duplicate it. The experimental evidence packager preserves Android CLI Journey reports and packages linked screenshots and explicitly supplied metadata/artifacts into a portable ZIP.

![Status](https://img.shields.io/badge/status-experimental-orange)
![License](https://img.shields.io/badge/license-Apache--2.0-22c55e)
![Local first](https://img.shields.io/badge/local--first-no%20cloud%20upload-7c3aed)

## Why this is changing

Google's Android CLI now provides SDK and emulator workflows, app deployment, device inspection, agent skills, and Journeys. Rebuilding those capabilities would create unnecessary duplication.

This repository is testing a narrower idea: make the evidence from an agent-run Android test easier to preserve, verify, and share. The existing ADB scripts, Python CLI, and DeepSeek Harness integration remain available for compatibility, but are legacy functionality under review—not the long-term product direction.

## Experimental evidence packager

Run a Journey with the official Android CLI first. Then package its Markdown report and local screenshot references:

```bash
python tools/evidence_pack.py \
  --report artifacts/journey.md \
  --output artifacts/android-evidence.zip
```

The archive contains the original report, a JSON manifest, SHA-256 checksums, locally linked evidence, and any extra files explicitly supplied with `--artifact`.

See [docs/EVIDENCE-BUNDLES.md](docs/EVIDENCE-BUNDLES.md) for metadata, safety behavior, limitations, and examples. This utility does not run tests or control an emulator.

## Legacy toolkit (under review)

The existing provisioning scripts, ADB Python CLI, and agent integrations are retained for compatibility while the project direction is validated. For new Android setup, device interaction, and Journey workflows, start with the [official Android CLI](https://developer.android.com/tools/agents/android-cli).

## Quick start

1. Install [Android Studio](https://developer.android.com/studio).
2. In SDK Manager, install Android SDK Platform-Tools, Android Emulator, and a Google Play system image for an API level supported by your app.
3. Create a Pixel virtual device in Device Manager using the Google Play image and boot it.

Or create an AVD from the command line:

**Linux / macOS**
```bash
chmod +x scripts/bootstrap-avd.sh
./scripts/bootstrap-avd.sh 35
emulator -avd Pixel_Play_API_35
```

The provisioning scripts validate their API and AVD-name inputs, fail if SDK
licenses cannot be accepted, and verify that the AVD configuration was created.

**Windows PowerShell**
```powershell
.\scripts\bootstrap-avd.ps1 -Api 35
emulator -avd Pixel_Play_API_35
```

Verify the device:

```bash
adb devices -l
python tools/android_lab.py devices
python tools/android_lab.py doctor --json
python tools/android_lab.py verify --serial emulator-5554
```

## Agent integrations

### Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R .claude/skills/android-emulator-lab ~/.claude/skills/
```

### OpenAI Codex

The repository includes a project-local skill under `.agents/skills/android-emulator-lab/`.

### DeepSeek Harness

From the repository root:

```bash
dsh plugin --profile tui add file:./dsh-plugin
dsh --profile tui
```

Replace `tui` with your profile name. The plugin expects `adb` on PATH; set `ANDROID_ADB` to an explicit executable path if needed.

**Compatibility note:** the DSH integration is supplied as a local bundle. Verify it against the exact Harness/Cordis version you run because plugin APIs can evolve.

## Included tooling

The standard-library Python CLI at `tools/android_lab.py` supports:

- Listing connected ADB devices
- Verifying device information and Google Play packages
- Installing APKs and launching installed apps
- Capturing screenshots and dumping the UI hierarchy
- Retrieving logcat output

The DeepSeek plugin exposes focused tools for device discovery, AVD boot/wait, APK install/launch, screenshots, UI inspection, taps, swipes, text input, key events, and Google Play Services checks. Device-changing operations require an explicit target serial.

For Google's supported agent-native workflows and Journeys, use the [official Android CLI documentation](https://developer.android.com/tools/agents/android-cli). The old Appium and test strategy documents remain useful for legacy setups.

## Know the boundaries

A Google Play AVD is useful, but it is **not a physical certified handset**. Play Integrity, hardware-backed attestation, NFC, Bluetooth peripherals, cellular behavior, DRM, and some push-notification paths may differ or require real hardware. Emulator camera input is simulated or forwarded from a host webcam.

Use a real device for final validation of hardware-dependent or device-integrity-dependent behavior.

## Security

- Use a dedicated test Google account and synthetic test data.
- Never put credentials, tokens, or secrets in prompts, source files, screenshots, or logs.
- Avoid testing real banking, payment, messaging, or medical accounts with an autonomous agent.
- Review screenshots and logs before sharing; they may contain personal data.
- Do not install APKs from untrusted sources.

## Repository layout

```text
.claude/skills/       Claude Code skill
.agents/skills/       Codex project-local skill
skills/               Portable skill source
scripts/              Windows and Unix AVD bootstrap scripts
tools/                Agent-friendly Python CLI
dsh-plugin/           DeepSeek Harness bundle plugin
docs/                 Appium and test strategy guides
tests/                Static smoke checks
.github/workflows/    GitHub Actions validation
```

## Contributing

Issues, compatibility reports, tested workflows, and pull requests are welcome. Particularly useful contributions include OS-specific validation, tested Harness-version compatibility, and reproducible camera / Appium examples.

## License

Apache-2.0. See [LICENSE](LICENSE).

## References

- [Android Emulator documentation](https://developer.android.com/studio/run/emulator)
- [AVD command-line documentation](https://developer.android.com/studio/run/emulator-commandline)
- [Android SDK tools](https://developer.android.com/tools)
- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)

---
**Built for local-first, agent-driven Android testing.**


## Python CLI interaction commands

The stdlib-only CLI supports explicit-target boot readiness, APK install/launch, package metadata, taps, swipes, constrained text entry, navigation key events, screenshots, UI hierarchy dumps, logcat, and app force-stop. Run `python tools/android_lab.py --help` for the full command list. Every device operation requires `--serial`; the CLI never guesses which emulator to control. Text entry intentionally accepts a conservative ASCII subset; use Appium for Unicode and selector-based interaction.

Commands also accept `--json` for machine-readable output, for example:
`python tools/android_lab.py devices --json` or
`python tools/android_lab.py verify --serial emulator-5554 --json`.
The `doctor` command checks ADB availability and whether at least one device is ready;
it does not select a target. With `--json`, command failures are emitted as
`{"ok": false, "error": "..."}` on stderr and retain a non-zero exit code.

The emulator integration checks are opt-in and require a booted device:

```bash
ANDROID_LAB_INTEGRATION=1 ANDROID_SERIAL=emulator-5554 \
python -m unittest tests.test_integration_android_lab -v
```
