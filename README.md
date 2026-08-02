# Safar Agent

A daily content agent for **Safar car perfumes** (5 fragrances, signature
diamond-cut bottle). Every day it:

1. Picks a **fragrance of the day** — Mon–Fri rotate through the 5 scents,
   weekends spotlight the diamond bottle itself.
2. Picks a **creative theme** (action-figure diorama, movie parody, meme
   format, POV driver humor, ASMR unboxing, festival tie-ins, and 15 more —
   see `src/safar_agent/content/themes.py`) that wasn't used in the last week.
3. Uses GPT to write the caption, hashtags, on-image text, and a short video
   script for that fragrance + theme combo.
4. Composes a feed image from **your uploaded product photos**.
5. Renders a ~15s vertical **short** (Ken Burns zoom + captions + voiceover)
   every day, and a longer **weekly showcase video** across all 5 fragrances
   once a week.
6. Publishes the image to **Facebook** + **Instagram**, the short to
   **Instagram Reels** + **YouTube Shorts**, and the weekly video to
   **YouTube**.
7. Logs everything to `data/history.json` so themes don't repeat too soon.

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
```

Copy `.env.example` to `.env` and fill in what you have so far — you can do
this incrementally (see below, everything degrades gracefully in dry-run).

## 3. Try it in dry-run first

```bash
cp .env.example .env   # add at least OPENAI_API_KEY
python -m safar_agent.scheduler.daily_job
```

This generates today's image + short video (and the weekly video, on
`WEEKLY_VIDEO_WEEKDAY`) into `output/<today>/` **without posting anywhere**.
Look at the output, tweak `data/products.yaml` / `content/themes.py` / the
prompt in `content/idea_generator.py` until you're happy with the voice.

## 4. Connect the real accounts

Each of these is a real platform integration, and each requires credentials
only you can generate:

### OpenAI
- `OPENAI_API_KEY` from platform.openai.com.
- `OPENAI_TEXT_MODEL` — set to whichever GPT-5-family model your account has
  access to (defaults to `gpt-5`).

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
   it posts — it can't accept uploaded bytes directly. Configure a media
   host: the simplest is an S3 bucket (`AWS_S3_BUCKET`, `AWS_ACCESS_KEY_ID`,
   `AWS_SECRET_ACCESS_KEY`, `PUBLIC_MEDIA_BASE_URL`), or swap
   `src/safar_agent/publishers/media_host.py` for Cloudinary/GCS/whatever you
   already use.

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

Two options — pick one (or both: keep GitHub Actions as a backup that fires
if your laptop happens to be off).

### Option A: your Mac (launchd) — runs locally, no cloud account needed

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

### Option B: GitHub Actions (cloud, always-on regardless of your laptop)

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
assets/products/<id>/               your uploaded photos, per fragrance
assets/audio/bg_music.mp3           optional background music bed (add your own)
src/safar_agent/
  content/themes.py                theme bank (add/edit ideas here)
  content/idea_generator.py        GPT prompt -> caption/hashtags/video script
  content/image_generator.py       photo -> branded feed image
  video/daily_short.py             15s vertical short (Ken Burns + captions + VO)
  video/weekly_video.py            landscape multi-fragrance showcase video
  publishers/facebook.py           Graph API photo/video posting
  publishers/instagram.py          Graph API container -> publish flow
  publishers/youtube.py            resumable video upload
  scheduler/daily_job.py           orchestrates the whole daily run
scripts/youtube_oauth_setup.py     one-time OAuth flow to get a refresh token
scripts/install_launchd.sh         registers the daily job as a macOS launchd agent
scripts/run_daily.sh               wrapper launchd calls (activates venv, runs the job)
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
