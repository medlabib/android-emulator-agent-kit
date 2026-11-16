# Android CLI pivot: product gap analysis

**Status:** initial evidence-based assessment  
**Date:** 2026-11-16  
**Repository:** [android-emulator-agent-kit](https://github.com/medlabib/android-emulator-agent-kit)

## Executive decision

Stop building a second Android command-line toolkit.

Google's Android CLI now covers most of the original project's advertised surface: SDK and AVD management, app installation and launch, selector-based UI input, screenshots and annotated screen inspection, UI hierarchy output, agent skills, Android Studio integrations, and agent-driven Journeys.

The project should become a **complementary test-evidence and workflow layer** that uses Android CLI as its primary Android interface. It should not reimplement ADB wrappers, emulator management, UI selectors, or generic Android skills unless a measured compatibility gap requires a narrowly scoped fallback.

Do not rename the repository or delete existing integrations yet. First prove the proposed gap with a small prototype and real CI/device experiments.

## 1. Capability comparison

| Area | Official Android CLI | Current repository | Decision |
|---|---|---|---|
| SDK setup and updates | `android sdk`, `android update` | Shell/PowerShell provisioning scripts | Prefer official CLI; keep only tested presets or platform workarounds |
| AVD lifecycle | `android emulator create/list/start/stop` | Custom AVD bootstrap scripts and DSH boot tools | Retire duplicate lifecycle logic after validating target profiles and Windows support |
| Install and launch | `android install`, `android run` | Python and DSH ADB wrappers | Remove from core roadmap |
| UI interactions | `android input` supports selector-based tap, swipe, scroll, text, and keys | Coordinate-based Python ADB commands and DSH ADB tools | Prefer official selector-based input; avoid maintaining a parallel interaction API |
| Screen and UI inspection | `android screen`, `android layout` | Screenshot and UI-dump wrappers | Use official commands |
| Agent guidance | `android init`, `android skills` | Three copies of a custom Android skill | Reassess and reduce to project-specific workflows only |
| End-to-end journeys | Natural-language/XML Journeys evaluated by an agent; action-level result guidance and Markdown reporting | Test strategy document, no comparable journey engine | Integrate with Journeys rather than invent another test DSL |
| Profiling and artifact analysis | Official CLI includes profiler and analyze capabilities in current release notes | Not implemented | Do not duplicate |
| CI and result packaging | Journeys can be used in CI; documentation describes Markdown result files and screenshots | Basic GitHub Actions static checks and opt-in emulator smoke tests | Candidate gap: normalize, preserve, and publish evidence consistently |

References:
- [Android CLI overview](https://developer.android.com/tools/agents/android-cli)
- [Android CLI command reference](https://developer.android.com/tools/agents/android-cli/commands)
- [Android CLI input](https://developer.android.com/tools/agents/android-cli/commands/input)
- [Android CLI Journeys](https://developer.android.com/tools/agents/android-cli/journeys)
- [Journey authoring/evaluation reference](https://developer.android.com/agents/skills/devtools/android-cli/references/journeys)
- [Android CLI release notes](https://developer.android.com/tools/agents/android-cli/release-notes)

## 2. What is genuinely different enough to investigate?

The strongest candidate is not another way to tap a button. It is a reliable, portable **test evidence bundle** around a test run.

A proposed bundle could contain:

- Run metadata: git commit, build identifier, app package/version, APK SHA-256, Android CLI version, device serial/model/API, host OS, and timestamps.
- Journey source and the exact command/instructions used.
- Per-step status and failure reason, retaining the original Journey report as source evidence.
- Screenshots, UI layout snapshots, and focused logcat excerpts captured at meaningful checkpoints.
- Crash/ANR signals where available, with clear distinction between observed facts and inferred diagnoses.
- A machine-readable JSON manifest plus a human-readable Markdown/HTML report.
- Optional JUnit XML and GitHub Actions annotations, **only after proving that existing Android CLI/Gradle/Journey outputs do not already provide an equivalent reliable format**.
- A deterministic archive with checksums, suitable for CI artifacts and sharing in bug reports.

This is a hypothesis, not yet a claim that Google lacks these features. Validate output formats, artifact locations, exit codes, CI behavior, and failure semantics against the current installed Android CLI before implementing the layer.

## 3. Proposed product boundary

### Use Android CLI for

- SDK and emulator management.
- APK install/build/run.
- UI selectors and gestures.
- Screenshots, annotated screens, and layout inspection.
- Official Android skills and documentation.
- Agent-driven Journeys.
- Profiling and artifact analysis when available.

### Own only the complementary layer

1. **Run orchestration:** a thin, documented entry point that invokes supported Android CLI commands and never shadows their semantics.
2. **Evidence collection:** collect the exact outputs and artifacts for a run without silently changing or resetting the device.
3. **Failure context:** correlate Journey failures with timestamps, logcat, crashes, ANRs, app version, and environment metadata.
4. **Report normalization:** preserve original outputs and produce stable JSON/Markdown; add JUnit/GitHub formats only if they are truly missing.
5. **CI packaging:** upload evidence bundles and make failures understandable from a pull request.
6. **Agent adapters:** optional thin adapters for agents not covered by Google's official plugins, such as DeepSeek Harness, only if they add real value.

## 4. Audit findings in the current repository

### High-priority defect

`scripts/bootstrap-avd.sh` references `$CONFIG` before assigning it:

```bash
if [[ ! -f "$CONFIG" ]]; then
  echo "AVD configuration was not created: $CONFIG" >&2
  exit 1
fi
CONFIG="$HOME/.android/avd/${AVD}.avd/config.ini"
```

Because the script enables `set -u`, this can terminate the script with an unbound-variable error after creating the AVD. Define the AVD config path before checking it, and respect `ANDROID_AVD_HOME` where set.

### Product duplication

- `tools/android_lab.py` duplicates device discovery, boot checks, APK installation, launch, taps, swipes, text entry, screenshots, and UI dumps.
- `dsh-plugin/index.js` implements many of the same operations directly through ADB.
- The custom skills teach the same manual ADB workflows that official Android CLI skills now cover.
- The README currently markets the duplicate surface as the primary value proposition.

These should be deprecated or converted to thin compatibility adapters after the official CLI dependency and version behavior are tested. Do not remove them in one destructive change.

### Test coverage and CI limitations

- Unit tests cover a small subset of the Python wrapper's validation and command behavior.
- Emulator integration tests are opt-in and skipped unless a configured device is available.
- The integration suite currently checks boot/package verification and UI hierarchy retrieval; it does not exercise a complete Journey, collect a full evidence bundle, or validate CI report publication.
- The latest observed main-branch Actions run for commit `ab0c1e88f4f2b93826f6b012e07ad99a83ac4fcb` ended with `action_required`; inspect the run and repository approval settings rather than interpreting it as a passing test.

### Documentation drift

The README still leads with the old ADB/Python toolkit positioning. Its CLI reference and setup instructions should be rewritten after the pivot implementation is validated.

## 5. Validation plan before choosing the implementation

Run this experiment on a clean Linux/macOS host and, separately, Windows where supported:

1. Install/update Android CLI and record `android --version`, `android help`, and relevant subcommand help.
2. Run `android emulator list`, create/start a test AVD, and record all generated files and outputs.
3. Install and launch a sample APK using official commands.
4. Inspect the UI using `android layout` and `android screen`; interact using selector-based `android input`.
5. Author and run a small Journey containing successful steps, a deliberate failed expectation, and a simulated app crash if practical.
6. Record exact exit codes, stdout/stderr, generated report files, screenshot locations, and whether artifacts are stable in CI.
7. Determine whether Journey reports already expose reliable machine-readable step results or only agent-authored Markdown.
8. Test logcat/crash/ANR collection and timestamp correlation without modifying the app or device state.
9. Verify which operations require network access, Google authentication, an agent, Android Studio, or a physical device.
10. Compare the same run in GitHub Actions and a local developer environment.

Do not implement a report converter until this experiment identifies a concrete missing format or reliability issue.

## 6. First implementation milestone

After the validation experiment, build the smallest useful proof:

- A manifest/schema for a test run and its artifacts.
- A collector that gathers official Journey outputs plus selected device diagnostics.
- A Markdown summary and JSON manifest that link to the original evidence.
- A deterministic ZIP bundle with SHA-256 checksums.
- A sample GitHub Actions workflow that runs a Journey and uploads the bundle.
- Tests using fixture Journey reports and mocked command outputs; keep emulator tests opt-in.

Keep the original Journey report untouched. Never fabricate a PASS, infer a crash from a missing screenshot, or classify an ambiguous result as a failure without evidence.

## 7. Non-goals

- Replacing Google's Android CLI.
- Creating another ADB abstraction or UI selector language.
- Recreating Android Studio Journeys.
- Building a cloud device farm.
- Sending screenshots, logs, or source code to a hosted service by default.
- Claiming emulator coverage proves physical-device compatibility.

## 8. Acceptance criteria

The pivot is successful only if a developer can run an Android CLI Journey and receive a portable, reproducible evidence bundle that:

- identifies exactly what was tested and on which build/device;
- preserves the original Journey result and source artifacts;
- contains useful logs/screenshots/layout evidence for failures;
- can be consumed by both a human and CI;
- does not reimplement functionality already provided by Android CLI;
- clearly marks missing or unavailable evidence instead of inventing it.

**Product principle:** Android CLI does the Android work. This project makes the test run, its evidence, and its failures easier to trust, reproduce, and share.
