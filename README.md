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
assets/products/oud-voyage/
assets/products/citrus-drift/
assets/products/musk-highway/
assets/products/lavender-cruise/
assets/products/woody-trail/
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

### Facebook Page
1. Create a Meta developer app at developers.facebook.com.
2. Get a Page Access Token for your Safar page with
   `pages_manage_posts` + `pages_read_engagement` scopes, and exchange the
   short-lived token for a long-lived one (Meta's Graph API Explorer /
   Access Token Debugger walks you through this).
3. Set `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN`.

### Instagram
Instagram posting goes through the **same** Graph API app/token as Facebook,
against your Instagram **Business/Creator** account linked to that Page.
1. Set `IG_BUSINESS_ACCOUNT_ID` (find it via
   `GET /{page-id}?fields=instagram_business_account`).
2. Instagram's API requires a **public URL** for any image/video it posts —
   it can't accept uploaded bytes directly. Configure a media host: the
   simplest is an S3 bucket (`AWS_S3_BUCKET`, `AWS_ACCESS_KEY_ID`,
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
