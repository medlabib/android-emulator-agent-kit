---
name: android-emulator-lab
description: Set up, boot, inspect, and test Android apps on a local Android Studio emulator with Google Play services using ADB. Use when building or validating Android, Flutter, React Native, or Expo apps; installing APKs; testing UI flows, permissions, camera simulation, crashes, or collecting screenshots and logcat evidence.
---

# Android Emulator Lab

Use this skill to operate a local Android Studio AVD as a repeatable test device. Prefer a **Google Play** AVD image when the app needs Google Play Store or Google Play Services.

## First principles

- This is a local emulator workflow, not a cloud phone.
- A Google Play AVD is not equivalent to a certified physical handset. Do not claim that Play Integrity, NFC, Bluetooth, telephony, Wallet, DRM, or hardware-backed attestation has been validated unless tested on appropriate real hardware.
- Emulator camera input is simulated or forwarded from a host webcam. Verify camera behavior in-app; do not describe it as a physical phone camera.
- Never invent test results. Capture evidence and report what was actually observed.
- Do not use production credentials or real personal data. Use a dedicated test account and synthetic fixtures.
- Do not run destructive actions, send messages, make calls, spend money, or alter real accounts without explicit user approval.

## Environment discovery

Run:
```bash
adb version
adb devices -l
emulator -list-avds
```

If `adb` is not on PATH, locate Android SDK Platform-Tools and either add `<ANDROID_SDK_ROOT>/platform-tools` to PATH or use the absolute adb path. Common SDK locations:

- macOS: `~/Library/Android/sdk`
- Linux: `~/Android/Sdk`
- Windows: `%LOCALAPPDATA%\Android\Sdk`

Check the emulator executable:
```bash
emulator -version
```

If multiple devices are attached, always use `adb -s <serial> ...`. Never silently choose a target.

## Create a Google Play AVD

1. Open Android Studio → SDK Manager.
2. Install an Android platform with a system image explicitly labelled **Google Play**.
3. Install Android Emulator and Android SDK Platform-Tools.
4. Device Manager → Create Virtual Device → choose a Pixel profile.
5. Select the **Google Play** system image (not AOSP; Google APIs alone may not include the Play Store app).
6. In advanced AVD settings configure front/back camera as `webcam0` if supported by the host, otherwise `Emulated`.
7. Boot and verify:
```bash
emulator -avd <AVD_NAME>
adb devices -l
adb -s <SERIAL> shell getprop sys.boot_completed
adb -s <SERIAL> shell pm list packages | grep -E 'com.android.vending|com.google.android.gms'
```
Windows PowerShell alternative:
```powershell
adb -s <SERIAL> shell pm list packages | Select-String 'com.android.vending|com.google.android.gms'
```

## Build and install

For Gradle projects, inspect the repository before choosing a build task:
```bash
./gradlew tasks
```
Typical debug build:
```bash
./gradlew assembleDebug
```
Find the APK under the app module's `build/outputs/apk/debug/`. Then:
```bash
adb -s <SERIAL> install -r path/to/app-debug.apk
```
Do not assume the module is named `app`; inspect Gradle settings and outputs.

## Launch and observe

Launch by package:
```bash
adb -s <SERIAL> shell monkey -p <APPLICATION_ID> 1
```
Capture screenshot:
```bash
adb -s <SERIAL> exec-out screencap -p > artifacts/screen.png
```
Dump accessibility/UI hierarchy:
```bash
adb -s <SERIAL> shell uiautomator dump /sdcard/window.xml
adb -s <SERIAL> shell cat /sdcard/window.xml
```
Collect logs:
```bash
adb -s <SERIAL> logcat -d -t 3000
```

## UI interaction

Use stable selectors when possible: Android UI Automator / Appium selectors, accessibility labels, and resource IDs. Inspect the UI hierarchy before coordinate taps.

ADB input examples:
```bash
adb -s <SERIAL> shell input tap 500 900
adb -s <SERIAL> shell input swipe 500 1200 500 300 350
adb -s <SERIAL> shell input keyevent 4
```
Coordinate-based interaction is a fallback. Re-screenshot after each meaningful state transition and verify the expected result.

## Camera testing

- Inspect the AVD's camera configuration in Device Manager.
- Use `webcam0` for host webcam forwarding when available, or `Emulated` for synthetic input.
- Verify permission prompts, allow/deny/revoke behavior, preview rendering, capture output, rotation, background/foreground transitions, and camera-unavailable handling.
- Do not claim that a successful emulator test proves compatibility with all physical cameras or OEM camera stacks.
- If the test requires photographing a real physical scene, use a real Android handset with USB debugging and an approved test environment.

## Test protocol

1. Translate the request into observable acceptance criteria.
2. Confirm the target device serial and Android version.
3. Install or update the debug APK.
4. Reset app state only if requested or necessary, and disclose when you do.
5. Execute one flow at a time.
6. Capture screenshots at important checkpoints.
7. Inspect UI hierarchy and logcat when behavior is unexpected.
8. Reproduce failures once with a clean, documented sequence.
9. Report pass/fail/blocked per criterion, with evidence paths and relevant log excerpts.
10. Separate emulator limitations from application defects.

## Failure triage

- Install failure: inspect package ABI, minSdk, signing, and `adb install` output.
- App crash: collect `logcat`, identify FATAL EXCEPTION and process PID, then reproduce.
- UI not found: refresh UI hierarchy; check dialogs, WebViews, Compose semantics, and accessibility labels.
- App appears frozen: inspect ANR traces and logcat; do not infer a crash from a slow screen.
- Play services unavailable: verify that the AVD uses a Google Play image and that setup/updates have completed.
- Camera black screen: check AVD camera source, host webcam permissions, app camera permission, and whether another process owns the webcam.

## Final report format

```text
Environment
- AVD/device:
- Android/API:
- Google Play Store:
- Google Play Services:
- Camera source:

Build
- Command:
- Result:
- APK:

Test results
- [PASS|FAIL|BLOCKED] Criterion — evidence
- ...

Defects
- Reproduction:
- Expected:
- Actual:
- Logs/screenshots:

Limitations
- Emulator-specific caveats:
```


## CLI reference

```bash
python tools/android_lab.py devices
python tools/android_lab.py doctor --json
python tools/android_lab.py wait-boot --serial emulator-5554
python tools/android_lab.py verify --serial emulator-5554
python tools/android_lab.py install --serial emulator-5554 --apk path/to/debug.apk
python tools/android_lab.py launch --serial emulator-5554 --package com.example.app
python tools/android_lab.py app-info --serial emulator-5554 --package com.example.app
python tools/android_lab.py tap --serial emulator-5554 --x 540 --y 900
python tools/android_lab.py swipe --serial emulator-5554 --x1 540 --y1 1500 --x2 540 --y2 400
python tools/android_lab.py type --serial emulator-5554 --text 'test account'
python tools/android_lab.py keyevent --serial emulator-5554 --key BACK
python tools/android_lab.py screenshot --serial emulator-5554
python tools/android_lab.py ui-dump --serial emulator-5554
python tools/android_lab.py logcat --serial emulator-5554 --filter FATAL
python tools/android_lab.py force-stop --serial emulator-5554 --package com.example.app
```

Text entry is limited to a conservative ASCII subset to avoid shell metacharacter surprises. Use Appium for Unicode, complex input, and selector-based interaction. Force-stop terminates the app process but does not clear app data. No command silently selects a device.
Use `doctor` before selecting a serial when diagnosing setup failures. With `--json`, errors are machine-readable on stderr and commands preserve non-zero exit codes.
