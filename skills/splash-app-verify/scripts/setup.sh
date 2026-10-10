#!/usr/bin/env bash
# Prepare a machine to run uitest.py: a card-host build and, on Linux without a
# display, Xvfb with Mesa's software OpenGL. Safe to run again.
#
#   skills/splash-app-verify/scripts/setup.sh [path/to/OctoSense-App-Hub]
#
# It installs system packages only with your confirmation (apt-get), builds
# card-host with cargo when none is found, and finishes with `uitest.py doctor`.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
hub="${1:-${OCTOSENSE_APP_HUB:-}}"
if [ -z "$hub" ]; then
  for c in "$here/../../../../OctoSense-App-Hub" "$here/../../../../octosense-app-hub"; do
    [ -d "$c" ] && hub="$(cd "$c" && pwd)" && break
  done
fi

if [ "$(uname -s)" = "Linux" ]; then
  need=()
  command -v Xvfb >/dev/null || need+=(xvfb xauth)
  command -v pkg-config >/dev/null || need+=(pkg-config)
  # Build-time headers for card-host; at run time only Xvfb and Mesa are used.
  dpkg -s libwayland-dev >/dev/null 2>&1 || need+=(libwayland-dev libxkbcommon-dev libx11-dev libxcursor-dev libxrandr-dev libxi-dev libasound2-dev libpulse-dev libgl-dev libegl-dev libdrm-dev libssl-dev)
  dpkg -s libgl1-mesa-dri >/dev/null 2>&1 || need+=(libgl1-mesa-dri)
  if [ ${#need[@]} -gt 0 ]; then
    echo "Packages to install: ${need[*]}"
    read -r -p "Install them with apt-get? [y/N] " ok
    if [ "${ok:-n}" = "y" ]; then
      sudo apt-get update -q && sudo apt-get install -y -q "${need[@]}"
    else
      echo "Skipped; uitest.py doctor will say what is missing."
    fi
  fi
fi

if [ -z "${OCTO_CARD_HOST:-}" ] && ! command -v card-host >/dev/null; then
  if [ -n "$hub" ] && [ -x "$hub/target/release/card-host" ]; then
    echo "card-host: $hub/target/release/card-host"
  elif [ -n "$hub" ]; then
    echo "Building card-host in $hub (first build takes a while)…"
    (cd "$hub" && cargo build --release -p octosense-card-host)
  else
    echo "No OctoSense-App-Hub checkout found: pass its path, or set OCTO_CARD_HOST." >&2
  fi
fi

if [ -n "$hub" ] && [ -x "$hub/target/release/card-host" ] && [ -z "${OCTO_CARD_HOST:-}" ]; then
  export OCTO_CARD_HOST="$hub/target/release/card-host"
  echo "Set OCTO_CARD_HOST=$OCTO_CARD_HOST for this shell; add it to your profile to keep it."
fi
python3 "$here/uitest.py" doctor
