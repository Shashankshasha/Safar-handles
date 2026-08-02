#!/bin/bash
# One-time setup: registers the daily job as a macOS launchd agent so it runs
# automatically every day, as long as your laptop is on (or wakes from sleep
# around the scheduled time).
#
# Usage:
#   ./scripts/install_launchd.sh          # uses OpenAI/Anthropic API (run_daily.sh)
#   ./scripts/install_launchd.sh claude   # uses your Claude subscription instead
#                                          # (run_daily_claude.sh, via the
#                                          # safar-daily-post skill + `claude -p`)
set -euo pipefail

MODE="${1:-api}"
case "$MODE" in
  api) RUN_SCRIPT="run_daily.sh" ;;
  claude) RUN_SCRIPT="run_daily_claude.sh" ;;
  *) echo "Usage: $0 [api|claude]"; exit 1 ;;
esac

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_NAME="com.safar.dailyjob.plist"
DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

mkdir -p "$HOME/Library/LaunchAgents"
sed -e "s|__REPO_DIR__|$REPO_DIR|g" -e "s|__RUN_SCRIPT__|$RUN_SCRIPT|g" \
  "$REPO_DIR/scripts/$PLIST_NAME.template" > "$DEST"

launchctl unload "$DEST" 2>/dev/null || true
launchctl load -w "$DEST"

echo "Installed and loaded $DEST"
echo "It will run scripts/$RUN_SCRIPT daily at 09:00 local time."
echo ""
echo "Useful commands:"
echo "  Run it right now (test):  launchctl start com.safar.dailyjob"
echo "  Check logs:               tail -f $REPO_DIR/output/launchd.log $REPO_DIR/output/launchd.error.log"
echo "  Uninstall:                launchctl unload $DEST && rm $DEST"
