# Android CLI Journey evidence bundles

The evidence packager is an **experimental post-run utility**. It does not run Journeys, control devices, call ADB, or replace Google's Android CLI. Run your Journey with the official tool first, then package its Markdown report and any locally linked screenshots/layout snapshots.

## Requirements

- Python 3.10 or newer (standard library only).
- An Android CLI Journey report in Markdown.
- Local screenshots or other files linked from that report, if you want them included.

## Basic usage

Suppose Android CLI produced `artifacts/journey.md` and the report links to screenshots relative to its own directory:

```bash
python tools/evidence_pack.py \
  --report artifacts/journey.md \
  --output artifacts/android-evidence.zip
```

The archive contains:

- `journey.md`: the original report, unchanged.
- `manifest.json`: schema version, creation timestamp, host Python/OS, best-effort Git commit, user-supplied metadata, artifact sizes and SHA-256 checksums.
- Local files referenced by Markdown links or images, preserving their relative paths.
- Any additional files explicitly supplied with `--artifact`.

Add build and device metadata using a JSON object:

```json
{
  "app": {
    "package": "com.example.myapp",
    "version": "1.4.2",
    "apk_sha256": "..."
  },
  "build": {
    "git_commit": "0123456789abcdef0123456789abcdef01234567",
    "workflow_run": "https://github.com/example/app/actions/runs/123"
  },
  "device": {
    "serial": "emulator-5554",
    "model": "Pixel_7",
    "android_api": 35
  }
}
```

Pass the metadata file and optional extra evidence:

```bash
python tools/evidence_pack.py \
  --report artifacts/journey.md \
  --metadata artifacts/run-metadata.json \
  --artifact artifacts/logcat.txt \
  --artifact artifacts/crash-info.txt \
  --output artifacts/android-evidence.zip
```

Example success output:

```json
{
  "output": "/workspace/artifacts/android-evidence.zip",
  "artifact_count": 4,
  "warning_count": 0,
  "manifest_schema": "1.0"
}
```

## Safety and current limitations

- The original Journey report is copied byte-for-byte; this tool does not reinterpret or change pass/fail results.
- Only local Markdown links/images that resolve to regular files inside the report directory are collected automatically. Absolute paths, path traversal, symlinks escaping the report directory, and remote URLs are not followed.
- Missing or unsafe local references are listed as warnings in the manifest. They do not silently disappear.
- Additional files are included only when explicitly passed with `--artifact`.
- The packager does not collect logcat, crash, ANR, device, or APK metadata itself. Supply those files/fields explicitly; a future adapter may gather them through supported Android CLI interfaces if a real gap is demonstrated.
- Review reports, screenshots, logs, and metadata before sharing. They may contain credentials, tokens, personal data, or internal URLs.
- The archive uses sorted entries and fixed ZIP timestamps, but its manifest includes a creation timestamp; therefore two runs are not byte-for-byte identical.

## Validation status

Unit tests cover report-link parsing, metadata validation, checksums, missing links, path traversal protection, and archive contents. A real Android CLI Journey and CI upload experiment are still required before calling this production-ready.

See [Android CLI Journeys](https://developer.android.com/agents/skills/devtools/android-cli/references/journeys) and the [official command reference](https://developer.android.com/tools/agents/android-cli/commands).
