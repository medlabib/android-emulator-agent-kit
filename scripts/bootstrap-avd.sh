#!/usr/bin/env bash
set -euo pipefail
API="${1:-35}"
AVD="${2:-Pixel_Play_API_${API}}"
if [[ ! "$API" =~ ^[0-9]+$ || "$API" -lt 21 || "$API" -gt 99 ]]; then
  echo "API must be an integer between 21 and 99." >&2
  exit 2
fi
if [[ ! "$AVD" =~ ^[A-Za-z0-9_.-]+$ ]]; then
  echo "AVD name contains unsupported characters." >&2
  exit 2
fi
SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
if [[ -z "$SDK" ]]; then
  case "$(uname -s)" in
    Darwin) SDK="$HOME/Library/Android/sdk" ;;
    Linux) SDK="$HOME/Android/Sdk" ;;
    *) echo "Set ANDROID_SDK_ROOT first." >&2; exit 2 ;;
  esac
fi
SDKMANAGER="$SDK/cmdline-tools/latest/bin/sdkmanager"
AVDMANAGER="$SDK/cmdline-tools/latest/bin/avdmanager"
if [[ ! -x "$SDKMANAGER" || ! -x "$AVDMANAGER" ]]; then
  echo "Install Android SDK Command-line Tools (latest) in Android Studio SDK Manager." >&2
  exit 2
fi
if ! yes | "$SDKMANAGER" --licenses >/dev/null; then
  echo "Unable to accept Android SDK licenses." >&2
  exit 2
fi
"$SDKMANAGER" "platform-tools" "emulator" "platforms;android-${API}" "system-images;android-${API};google_apis_playstore;x86_64"
if ! "$AVDMANAGER" list avd | grep -q "Name: ${AVD}$"; then
  echo "no" | "$AVDMANAGER" create avd --name "$AVD" --package "system-images;android-${API};google_apis_playstore;x86_64" --device "pixel_7"
fi
if [[ ! -f "$CONFIG" ]]; then
  echo "AVD configuration was not created: $CONFIG" >&2
  exit 1
fi
CONFIG="$HOME/.android/avd/${AVD}.avd/config.ini"
if [[ -f "$CONFIG" ]]; then
  for key in hw.camera.back hw.camera.front; do
    if grep -q "^${key}=" "$CONFIG"; then
      sed -i.bak "s|^${key}=.*|${key}=webcam0|" "$CONFIG"
    else
      echo "${key}=webcam0" >> "$CONFIG"
    fi
  done
fi
echo "Created/verified AVD: $AVD"
echo "Start with: emulator -avd \"$AVD\""
echo "If webcam0 is unavailable, edit Device Manager > AVD > Advanced Settings and select Emulated."
