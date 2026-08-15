#!/bin/bash
# Alternative to run_daily.sh: uses the safar-daily-post Claude Code skill
# (this repo's .claude/skills/safar-daily-post/) so caption writing runs on
# your Claude subscription via headless `claude -p`, instead of calling
# OpenAI/Anthropic's metered API. Image/video rendering and the actual
# posting still go through the same deterministic Python pipeline either way.
#
# --dangerously-skip-permissions is required for this to run unattended from
# launchd (no one is around to click "allow" on each tool call) — that means
# Claude executes the skill's bash commands without per-step confirmation.
# Run this manually a few times first and check output/<date>/ before
# trusting it on a schedule, and keep SAFAR_PUBLISH=false until you're happy
# with the output quality.
set -euo pipefail

# launchd runs scripts with a minimal PATH — it does NOT load your shell's
# .zprofile/.zshrc, so Homebrew tools (ffmpeg, and the `claude` CLI if it was
# installed via Homebrew) won't be found unless added here explicitly.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
source .venv/bin/activate

# Flip to "true" only after you've reviewed several dry runs in output/.
PUBLISH="${SAFAR_PUBLISH:-false}"

if [ "$PUBLISH" = "true" ]; then
  INSTRUCTION="Use the safar-daily-post skill to generate and PUBLISH today's Safar post for real (pass --publish to the pipeline command). The user has already approved automatic daily publishing for this scheduled run — do not ask for confirmation."
else
  INSTRUCTION="Use the safar-daily-post skill to generate today's Safar post as a DRY RUN only (do not pass --publish). Just generate and report the assets."
fi

claude -p "$INSTRUCTION" --dangerously-skip-permissions
