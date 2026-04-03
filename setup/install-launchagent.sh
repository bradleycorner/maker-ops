#!/bin/bash
# Installs the Maker-Ops API as a macOS launchd agent so it starts at login.
# Run from the project root: bash setup/install-launchagent.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_DST="$HOME/Library/LaunchAgents/com.makerops.api.plist"

echo "Project dir : $PROJECT_DIR"
echo "Installing  : $PLIST_DST"

# Unload existing agent if present
if launchctl list com.makerops.api &>/dev/null; then
    launchctl unload "$PLIST_DST" 2>/dev/null || true
fi

sed -e "s|PROJECT_DIR|$PROJECT_DIR|g" \
    -e "s|HOME_DIR|$HOME|g" \
    "$SCRIPT_DIR/com.makerops.api.plist.template" > "$PLIST_DST"

launchctl load "$PLIST_DST"
echo "Done. API will start at login and is running now."
echo "Logs: $HOME/Library/Logs/makerops-api.log"
