#!/bin/bash
# One-time setup: registers the daily job as a macOS launchd agent so it runs
# automatically every day, as long as your laptop is on (or wakes from sleep
# around the scheduled time).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_NAME="com.safar.dailyjob.plist"
DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

mkdir -p "$HOME/Library/LaunchAgents"
sed "s|__REPO_DIR__|$REPO_DIR|g" "$REPO_DIR/scripts/$PLIST_NAME.template" > "$DEST"

launchctl unload "$DEST" 2>/dev/null || true
launchctl load -w "$DEST"

echo "Installed and loaded $DEST"
echo "It will run scripts/run_daily.sh daily at 09:00 local time."
echo ""
echo "Useful commands:"
echo "  Run it right now (test):  launchctl start com.safar.dailyjob"
echo "  Check logs:               tail -f $REPO_DIR/output/launchd.log $REPO_DIR/output/launchd.error.log"
echo "  Uninstall:                launchctl unload $DEST && rm $DEST"
