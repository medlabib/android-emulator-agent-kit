# DSH Android Emulator Lab plugin

Install:
```bash
dsh plugin --profile tui add file:/absolute/path/to/android-emulator-agent-kit/dsh-plugin
```

Then:
```bash
dsh --profile tui
```

Requirements: Node.js 20+, Android SDK Platform-Tools, Android Emulator, and a DSH version compatible with `@deepseek-ai/dsh-tools` and `@deepseek-ai/cordis`.

Set `ANDROID_ADB` and `ANDROID_EMULATOR` if the binaries are not on PATH.

The plugin is deliberately local and ADB-based. It never exposes arbitrary shell execution and requires an explicit serial for target-specific actions.
