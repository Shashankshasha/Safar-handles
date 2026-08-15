# Safar Agent

A daily content agent for **Safar car perfumes** (5 fragrances, signature
diamond-cut bottle). Every day it:

1. Picks a **fragrance of the day** — Mon–Fri rotate through the 5 scents,
   weekends spotlight the diamond bottle itself.
2. Picks a **creative theme** (action-figure diorama, movie parody, meme
   format, POV driver humor, ASMR unboxing, festival tie-ins, and 15 more —
   see `src/safar_agent/content/themes.py`) that wasn't used in the last week
   — unless today is a listed special occasion (`data/occasions.yaml`:
   Independence Day, Republic Day, etc.), in which case that takes over as
   an occasion greeting instead. Add more occasions anytime, no code changes
   needed — just a `date: "MM-DD"` entry.
3. Uses an LLM — **GPT or Claude, your choice** — to write the caption,
   hashtags, on-image text, video script, and an **anime-character image
   prompt** for that fragrance + theme combo (see "Choosing a caption
   provider" below).
4. Builds the hero image one of three ways, depending on setup:
   - **`HERO_IMAGE_STYLE=anime`** (default): a Japanese anime/manga-style
     scene generated via OpenAI's image API — a different character and
     setting every day, the Safar diffuser visible in-scene. A few cents/day.
   - **`HERO_IMAGE_STYLE=photo`**: a plain photo+text composite from your
     uploaded product photo — free, zero image-generation calls.
   - If you run it via the `safar-daily-post` Claude Code skill: a
     Claude-designed cartoon/comic scene (free, embeds your real product
     photo, deliberately avoids repeating recent layouts) instead of either.
5. Renders a ~15s vertical **short** (Ken Burns zoom + captions + voiceover)
   every day, and a longer **weekly showcase video** across all 5 fragrances
   once a week (optionally opening with an OpenAI-generated cover illustration).
6. Publishes the image to **Facebook** + **Instagram**, the short to
   **Instagram Reels** + **YouTube Shorts**, and the weekly video to
   **YouTube**.
7. Logs everything to `data/history.json`, including a freeform note on each
   day's visual style, so neither the theme nor the look repeats too soon.

Everything runs in dry-run mode by default — it generates and saves the
assets under `output/<date>/` without posting anywhere, until you explicitly
turn on publishing (see below).

## 1. Add your product photos

Drop real photos of each fragrance / the diamond bottle into:

```
assets/products/musk/
assets/products/lavender/
assets/products/sandalwood/
assets/products/vanilla/
assets/products/jasmine/
assets/products/diamond-bottle-hero/   <- used for weekend posts + the weekly video
```

At least one photo per folder is required before that fragrance can be
posted. Fragrance names, taglines, scent notes and weekday assignment live in
`data/products.yaml` — edit that file if you want different names/copy or a
different day-of-week rotation.

## 2. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
# ffmpeg is required for video generation:
#   macOS:  brew install ffmpeg
#   Ubuntu: sudo apt-get install ffmpeg
# Only needed if you're using the safar-daily-post skill's cartoon scenes:
playwright install chromium
```

Copy `.env.example` to `.env` and fill in what you have so far — you can do
this incrementally (see below, everything degrades gracefully in dry-run).

## 3. Try it in dry-run first

```bash
cp .env.example .env   # add at least one of OPENAI_API_KEY / ANTHROPIC_API_KEY
python -m safar_agent.scheduler.daily_job
```

This generates today's image + short video (and the weekly video, on
`WEEKLY_VIDEO_WEEKDAY`) into `output/<today>/` **without posting anywhere**.
Look at the output, tweak `data/products.yaml` / `content/themes.py` / the
prompt in `content/providers/prompts.py` until you're happy with the voice.

### Choosing a caption provider (and comparing them)

Caption/hashtag/script generation is provider-agnostic — you can use OpenAI
GPT, Anthropic Claude, or both, and neither choice touches image/video
rendering or posting logic:

```bash
# Set a default in .env
TEXT_PROVIDER=openai      # or: anthropic

# Or override per run
python -m safar_agent.scheduler.daily_job --provider anthropic

# Generate today's caption from BOTH providers and compare, without
# touching images/video and without posting anywhere:
python -m safar_agent.scheduler.daily_job --compare-providers
```

`--compare-providers` prints both results and saves them to
`output/<today>/compare_providers.json` so you can judge quality/voice/cost
side by side before committing to one. You only need an API key for the
provider(s) you actually use — if you already pay for Claude, Anthropic
alone is enough to run the whole thing with no separate OpenAI billing setup.
Image generation (`content/image_generator.py`'s optional
`generate_ai_background`) is OpenAI-only regardless of `TEXT_PROVIDER`, but
composing images from your own uploaded photos (the default path) doesn't
call any image-generation API at all.

## 4. Connect the real accounts

Each of these is a real platform integration, and each requires credentials
only you can generate:

### Caption provider — OpenAI and/or Anthropic
You only need to fill in whichever of these you set as `TEXT_PROVIDER` (or
both, to use `--compare-providers`).

- **OpenAI**: `OPENAI_API_KEY` from platform.openai.com. `OPENAI_TEXT_MODEL`
  — whichever GPT-5-family model your account has access to (defaults to
  `gpt-5`).
- **Anthropic**: `ANTHROPIC_API_KEY` from console.anthropic.com.
  `ANTHROPIC_TEXT_MODEL` — defaults to `claude-sonnet-5`; `claude-haiku-4-5-20251001`
  is the cheapest option if cost is the deciding factor.

### Facebook Page + Instagram (one Meta app covers both)

For a single business posting to its own Page/Instagram account, you do
**not** need Meta's full App Review — that's only required when other
people's accounts will use your app. Keeping the app in **Development Mode**
with yourself as Admin is enough, and is much faster to set up:

1. Go to developers.facebook.com → **My Apps** → **Create App** → type
   "Business". Leave it in Development Mode.
2. Under **Add Product**, add **Facebook Login** and the **Graph API** (no
   review needed yet).
3. Make sure your personal Facebook account (the one that administers the
   Safar Page and its linked Instagram Business account) is listed as an
   **Admin** on the app, under App Roles.
4. Go to **Tools → Graph API Explorer**, pick your app, click **Generate
   Access Token**, and grant these permissions when prompted:
   `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`,
   `instagram_basic`, `instagram_content_publish`. Because you're an Admin on
   a Development-mode app, Meta grants these without review.
5. That token is short-lived (~1 hour). Exchange it for a long-lived
   Page Access Token (~60 days, and Pages tokens generated this way don't
   expire in practice as long as you keep re-deriving them the same way):
   ```
   GET https://graph.facebook.com/v19.0/oauth/access_token?
     grant_type=fb_exchange_token&client_id=<APP_ID>&client_secret=<APP_SECRET>
     &fb_exchange_token=<SHORT_LIVED_USER_TOKEN>
   ```
   then use that long-lived **user** token to fetch the Page token:
   ```
   GET https://graph.facebook.com/v19.0/me/accounts?access_token=<LONG_LIVED_USER_TOKEN>
   ```
   The `access_token` in that response, for your Safar Page, is what goes in
   `FB_PAGE_ACCESS_TOKEN`. Set `FB_PAGE_ID` from the same response.
6. Get your Instagram Business Account ID linked to that Page:
   ```
   GET https://graph.facebook.com/v19.0/{page-id}?fields=instagram_business_account&access_token={page-access-token}
   ```
   Set `IG_BUSINESS_ACCOUNT_ID` to the id it returns. (Your Instagram account
   must already be a Business/Creator account connected to the Facebook Page
   in Meta Business Suite — do that first if you haven't.)
7. Instagram's API additionally requires a **public URL** for any image/video
   it posts — it can't accept uploaded bytes directly. Two options are wired
   up (`MEDIA_HOST_PROVIDER` in `.env`):
   - **`github`** (free, no cloud account): commits each generated file to a
     dedicated `media` branch of this repo via the GitHub API and serves it
     via `raw.githubusercontent.com`. Requires **the repo to be public**
     (private-repo raw URLs need auth Instagram's servers can't provide) and
     permanently keeps every posted file in that branch's git history. Needs
     `GITHUB_TOKEN` — a personal access token (Settings → Developer settings
     → Personal access tokens → generate one scoped to Contents:
     read/write on this repo) — and `GITHUB_REPO` (`youruser/yourrepo`).
   - **`s3`**: needs an AWS account, bucket, and credentials
     (`AWS_S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
     `PUBLIC_MEDIA_BASE_URL`).

   Swap `src/safar_agent/publishers/media_host.py` for Cloudinary/GCS/
   whatever else if you'd rather use a different provider.

### YouTube
1. In Google Cloud Console, enable "YouTube Data API v3" and create an OAuth
   Client ID (type: Desktop app); download `client_secret.json` into
   `scripts/`.
2. Run `python scripts/youtube_oauth_setup.py` once, locally, signed in as
   the channel you want the agent to post as. It prints `YT_CLIENT_ID`,
   `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` — put those in `.env`.

### Turn publishing on
Set `DRY_RUN=false` in `.env`, then:

```bash
python -m safar_agent.scheduler.daily_job --publish
```

Both the env flag and the CLI flag have to agree to publish for real — this
is a deliberate double safety switch given it posts to public accounts.

## 5. Automate it daily

Three options — pick one (or combine: e.g. Claude subscription for captions,
GitHub Actions as a backup that fires if your laptop happens to be off).

### Option A: your Mac (launchd), captions via OpenAI/Anthropic API

1. Make sure `.venv` exists and dependencies are installed (Step 2 above) and
   your `.env` is filled in with `DRY_RUN=false`.
2. Register the daily job as a launchd agent:
   ```bash
   ./scripts/install_launchd.sh
   ```
   This installs `~/Library/LaunchAgents/com.safar.dailyjob.plist`, set to
   fire at **09:00 local time** every day (edit the `Hour`/`Minute` values in
   `scripts/com.safar.dailyjob.plist.template` and re-run the install script
   to change it).
3. Test it immediately without waiting for 9am:
   ```bash
   launchctl start com.safar.dailyjob
   tail -f output/launchd.log output/launchd.error.log
   ```
4. Caveats specific to running from a laptop: it only fires if the Mac is
   powered on; if it's asleep at 9am, launchd runs the job as soon as it
   wakes instead (not exactly on time, but it won't just skip the day). If
   the lid is closed and plugged in, macOS Power Nap / scheduled wake can
   keep it running on time — see System Settings → Battery → Options.
5. To uninstall: `launchctl unload ~/Library/LaunchAgents/com.safar.dailyjob.plist && rm ~/Library/LaunchAgents/com.safar.dailyjob.plist`.

### Option B: your Mac (launchd), captions via your Claude subscription instead of an API key

If you already pay for Claude Pro/Max and don't want to set up separate
OpenAI/Anthropic API billing, `.claude/skills/safar-daily-post/SKILL.md` has
Claude Code write the caption **and** design a fresh cartoon-style hero image
itself — a self-contained HTML/CSS "scene" (comic panels, mini dioramas,
meme layouts, etc., embedding your real product photo) rendered to PNG for
free via `scripts/render_scene.py` (headless Chromium). That's what keeps
every day's post genuinely different instead of the same photo with new text
on it. Video rendering and actual posting still run through the same Python
pipeline either way.

1. Install the [Claude Code CLI](https://claude.com/claude-code) and sign in
   with your subscription (`claude auth login`), from inside this repo so it
   picks up the skill.
2. Try it manually first, interactively, so you can watch what it does:
   ```bash
   claude
   > Use the safar-daily-post skill to generate today's Safar post as a dry run.
   ```
   Check `output/<date>/copy.json` and the generated image/video before
   trusting it unattended.
3. Register the launchd agent pointed at the Claude-driven script instead:
   ```bash
   ./scripts/install_launchd.sh claude
   ```
   This runs `scripts/run_daily_claude.sh`, which calls `claude -p` in
   headless mode. That requires `--dangerously-skip-permissions` (nothing's
   there to click "allow" at 9am) — read the comments at the top of that
   script before relying on it. It stays in dry-run mode by default; only
   set `SAFAR_PUBLISH=true` in the script (or `launchctl setenv`) once you've
   reviewed several days of dry-run output and are comfortable with it
   posting unattended.

### Option C: GitHub Actions (cloud, always-on regardless of your laptop)

`.github/workflows/daily-post.yml` runs the agent every day via GitHub
Actions cron (09:00 IST by default — edit the cron expression to taste).

Add every value from `.env` as a **repository secret** (Settings → Secrets
and variables → Actions) — non-sensitive ones like `OPENAI_TEXT_MODEL` or
`WEEKLY_VIDEO_WEEKDAY` can go in **Variables** instead. Scheduled runs always
publish for real; manual runs (`Actions` tab → "Run workflow") default to
dry-run with a checkbox to force a real publish, so you can test changes
safely.

## Project layout

```
data/products.yaml                 the 5 fragrances + diamond bottle + rotation
data/occasions.yaml                festival/national-day calendar (overrides theme rotation)
assets/products/<id>/               your uploaded photos, per fragrance
assets/audio/bg_music.mp3           optional background music bed (add your own)
src/safar_agent/
  content/themes.py                theme bank (add/edit ideas here)
  content/idea_generator.py        GPT prompt -> caption/hashtags/video script
  content/image_generator.py       photo -> branded feed image; OpenAI illustrated backgrounds
  video/daily_short.py             15s vertical short (Ken Burns + captions + VO)
  video/weekly_video.py            landscape multi-fragrance showcase video (+ optional AI cover art)
  publishers/facebook.py           Graph API photo/video posting
  publishers/instagram.py          Graph API container -> publish flow
  publishers/youtube.py            resumable video upload
  scheduler/daily_job.py           orchestrates the whole daily run
scripts/youtube_oauth_setup.py     one-time OAuth flow to get a refresh token
scripts/install_launchd.sh         registers the daily job as a macOS launchd agent
scripts/run_daily.sh               launchd wrapper: OpenAI/Anthropic API captions
scripts/run_daily_claude.sh        launchd wrapper: Claude subscription captions (headless claude -p)
scripts/print_today_brief.py       prints today's fragrance/theme/recent-visuals JSON, no LLM call
scripts/render_scene.py            renders a Claude-designed HTML scene to PNG (headless Chromium)
.claude/skills/safar-daily-post/   skill Claude Code follows to write copy + design the scene
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Covers the rotation/catalog logic (which fragrance/theme runs on which day,
no immediate theme repeats). It does not call any real API — content
generation, image/video rendering, and publishing all need live credentials
and real product photos to exercise end-to-end.
