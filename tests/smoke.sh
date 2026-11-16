#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile tools/android_lab.py
node --check dsh-plugin/index.js
echo "Static smoke checks passed. Runtime AVD/DSH/Appium tests require local dependencies and a booted emulator."
