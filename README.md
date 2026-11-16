# 🤖 Android Emulator Agent Kit

**A local Android phone for AI coding agents.**

Provision and control a Google Play-enabled Android Studio emulator from Claude Code, OpenAI Codex, or DeepSeek Harness. Install APKs, launch apps, inspect screens, interact through ADB, and collect logs — on your own machine.

![Version](https://img.shields.io/badge/version-0.2.0-2563eb)
![License](https://img.shields.io/badge/license-Apache--2.0-22c55e)
![Local first](https://img.shields.io/badge/local--first-ADB%20%2B%20AVD-7c3aed)

## Why this exists

AI agents can write Android code, but validating it often means manually opening Android Studio, booting a device, installing an APK, tapping through screens, and collecting logs. This project provides a repeatable, local-first workflow for those steps.

The recommended AVD uses a **Google Play** system image, including Play Store and Google Play Services. No device farm or cloud minutes are required.

## Capabilities

| Capability | Included |
|---|---|
| AVD provisioning | Windows PowerShell + Linux/macOS shell scripts |
| Google Play image | Yes, x86_64 system image |
| Claude Code skill | Included |
| OpenAI Codex skill | Included |
| DeepSeek Harness plugin | Bundled local plugin |
| APK install / launch | Python CLI + plugin tools |
| Screenshots, UI hierarchy, logcat | Yes |
| UI automation | ADB tap, swipe, text, keyevent; optional Appium 2 + UiAutomator2 |

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

**Windows PowerShell**
```powershell
.\scripts\bootstrap-avd.ps1 -Api 35
emulator -avd Pixel_Play_API_35
```

Verify the device:

```bash
adb devices -l
python tools/android_lab.py devices
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

For richer semantic selectors and test flows, see [docs/APPIUM.md](docs/APPIUM.md). For the recommended plan / act / observe loop, see [docs/TEST-STRATEGY.md](docs/TEST-STRATEGY.md).

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
