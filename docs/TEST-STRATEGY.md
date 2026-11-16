# Agent testing strategy

Use a plan/act/observe loop rather than unbounded tapping.

1. **Plan:** turn the requested scenario into numbered, observable acceptance criteria.
2. **Preflight:** confirm the exact ADB serial, Android/API version, boot state, Google Play packages, and camera source.
3. **Build:** inspect Gradle modules and build the correct debug variant; never assume `:app`.
4. **Install:** install only the intended artifact and record its SHA-256.
5. **Explore:** inspect screenshot + UI hierarchy before interacting. Prefer Appium selectors; use ADB coordinates only as fallback.
6. **Observe:** after each action, capture a screenshot and verify the expected state.
7. **Exercise edge cases:** permissions denied then granted, rotation, background/foreground, offline state, empty/invalid inputs, process recreation.
8. **Diagnose:** collect focused logcat and reproduce failures once from a documented clean state.
9. **Repair:** propose the smallest code change; do not silently modify production configuration or secrets.
10. **Retest:** rerun the failing scenario and relevant regression checks.
11. **Report:** PASS/FAIL/BLOCKED with evidence, environment, and emulator-specific limitations.

## Camera scenario checklist

- Confirm AVD camera source in Device Manager/config.ini.
- Confirm app camera permission and runtime permission flow.
- Verify preview appears and remains stable.
- Capture an image and verify a non-zero output file with a decodable image.
- Test app pause/resume and rotation.
- Test unavailable camera and permission denial.
- State explicitly whether input was a host webcam or emulator-generated scene.

## Not proven by a Google Play AVD

A Google Play system image provides Play Store and Google Play services packages, but does not prove Play Integrity certification or physical-device behavior. Use a certified physical handset for NFC, Bluetooth accessories, telephony, hardware attestation, OEM camera stacks, Wallet/banking workflows, and any release gate that depends on those features.
