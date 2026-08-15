#!/bin/bash
# Wrapper launchd calls. Activates the venv, loads .env, runs the daily job,
# and logs output so you can debug failures (e.g. laptop was asleep, no wifi).
#
# launchd runs scripts with a minimal PATH — it does NOT load your shell's
# .zprofile/.zshrc, so Homebrew tools like ffmpeg won't be found unless we
# add their directories here explicitly (this bit everyone the first time).
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

source .venv/bin/activate
python -m safar_agent.scheduler.daily_job --publish
