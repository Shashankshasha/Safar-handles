#!/bin/bash
# Wrapper launchd calls. Activates the venv, loads .env, runs the daily job,
# and logs output so you can debug failures (e.g. laptop was asleep, no wifi).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

source .venv/bin/activate
python -m safar_agent.scheduler.daily_job --publish
