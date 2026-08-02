---
name: safar-daily-post
description: Write today's Safar car-perfume caption AND design a fresh cartoon-style hero image yourself instead of calling an LLM/image API, then hand off video rendering and publishing to the existing Python pipeline. Use when asked to run today's Safar post, generate today's Safar caption/image, or do the daily Safar content task.
---

# Safar daily post

This repo already has a full pipeline for the Safar car-perfume brand
(`src/safar_agent/`): image composition, video rendering, and posting to
Facebook/Instagram/YouTube. Normally the caption is written by calling
OpenAI/Anthropic's API, and the hero image is either a plain photo+text
composite or an OpenAI-generated illustration. This skill has *you* do both
the caption **and** the image design directly instead — no `OPENAI_API_KEY` /
`ANTHROPIC_API_KEY` needed for either — so the whole thing runs on the user's
Claude subscription rather than metered API billing, and the daily visual
stays hand-designed and different every time instead of a repeating template.
Everything mechanical (which fragrance, video rendering, actual posting)
still goes through the same deterministic Python code — don't reimplement or
bypass that part.

The user cares specifically about **variety**: no two days should look or
read the same. Treat "another photo with text on it" as a failure mode to
actively avoid — that's what step 3 is for.

Run all commands from the repo root, with the venv active
(`source .venv/bin/activate`).

## Step 1 — Get today's brief

```bash
python scripts/print_today_brief.py
```

This prints JSON with today's `fragrance_id`, `fragrance_name`,
`fragrance_tagline`, `scent_notes`, `liquid_color`, `reference_photos` (paths
to the real uploaded product photos for today's fragrance), `theme_id`,
`theme_category`, `theme_hint`, `bottle_design`, and `recent_visual_notes`
(freeform descriptions of the last ~10 days' visual compositions — read
these and deliberately do something different: different layout, palette,
framing, or scene, not just a different theme).

The `theme_id` is randomly picked and **must** be echoed back verbatim in
step 2 — don't substitute a different theme even if you think of a better
one, since the history log has already logically reserved it for today.

## Step 2 — Write the copy

Write copy in this brand voice:

> You are the social media copywriter for Safar, a car-perfume brand by
> Grace One ("Invisible Luxury"). Safar sells 5 fragrances in a signature
> hanging car diffuser — a faceted diamond-cut glass bottle under a
> beech-wood pyramid cap on a braided cord, hung from the rearview mirror.
> Natural plant extracts, no added alcohol, heat resistant, lasts up to 60
> days — work these in naturally when relevant, don't force all of them into
> every post. The audience is car owners and drivers — funny, relatable,
> car-culture-savvy content performs best. Confident, witty, never salesy or
> corporate. Keep language simple enough for a broad Indian driving
> audience, mixing in light Hinglish where it feels natural.

Follow the brief's `theme_hint` for creative direction on today's post.

## Step 3 — Design today's cartoon scene

Design a self-contained HTML+CSS "scene" that visually executes today's
theme in an eye-catching, cartoon/illustrated style — think comic panels,
meme layouts, a tiny action-figure diorama, a mock movie poster, retro
cartoon backgrounds, etc. Pull creative range from the theme bank in
`src/safar_agent/content/themes.py` if you want more angles than the one
`theme_hint` gives you.

Guidelines:
- **Embed the real product photo** from `reference_photos` (step 1) as an
  `<img src="file:///absolute/path/...">` composited into the illustrated
  scene (e.g. sitting inside a cartoon-drawn car dashboard, held by an
  illustrated character, spotlighted in a diorama) — the post should still
  clearly show the actual product, not replace it with a generic drawing.
- Build everything else (backgrounds, characters, effects, speech bubbles,
  color treatment) with plain HTML/CSS/SVG — gradients, shapes, CSS
  illustration, inline SVG paths. No external assets/fonts/CDNs (the
  renderer has no network access).
- Vary the **layout structure** day to day, not just colors — check
  `recent_visual_notes` and pick something structurally different from what
  was just used.
- Canvas size: `1080x1350` for the feed image (matches Instagram/Facebook
  portrait). Set `body { margin:0; width:1080px; height:1350px; }`.

Save it to `output/<today's date, YYYY-MM-DD>/scene.html`, then render it:

```bash
python scripts/render_scene.py output/<date>/scene.html output/<date>/post.jpg --width 1080 --height 1350
```

(One-time setup if this errors about a missing browser:
`playwright install chromium`.)

Look at the rendered PNG/JPG before moving on — if it looks broken, cluttered,
or like a repeat of a recent layout, fix the HTML and re-render rather than
shipping it as-is.

Write down a short `visual_note` describing what you did (e.g. "3-panel comic
strip, orange/black palette, dashboard POV") — this goes in `_meta` below so
tomorrow's run knows to avoid repeating it.

## Step 4 — Assemble the copy JSON

Write a JSON file at `output/<date>/copy.json` with **exactly** this shape:

```json
{
  "concept": "one-line visual/creative concept — what the scene you built depicts",
  "instagram_caption": "...",
  "facebook_caption": "...",
  "youtube_short_title": "...",
  "youtube_short_description": "...",
  "on_image_text": "short punchy text, <=8 words (only used if you did NOT already bake text into the rendered scene)",
  "video_narration": "2-3 short spoken sentences for a 15-second vertical video voiceover, punchy and conversational",
  "hashtags": ["#...", "#...", "... 8-12 total, mix of brand + car + fragrance + trending-style tags"],
  "_meta": {
    "theme_id": "<the theme_id from step 1, unchanged>",
    "fragrance_id": "<the fragrance_id from step 1, unchanged>",
    "visual_note": "<short description of today's scene design, from step 3>"
  }
}
```

The `_meta` block is required — it's how the pipeline knows which theme you
wrote for and logs your visual note for next time.

## Step 5 — Hand off to the pipeline

Dry run first (always do this unless the user has explicitly confirmed they
want to publish for real):

```bash
python -m safar_agent.scheduler.daily_job --copy-file output/<date>/copy.json --image-file output/<date>/post.jpg
```

`--image-file` tells it to use your rendered scene instead of compositing a
plain photo+text image. Check the generated video in `output/<date>/` looks
right. Only add `--publish` once the user has explicitly confirmed — this
posts to real, public Facebook/Instagram/YouTube accounts, so don't pass it
unprompted or by default:

```bash
python -m safar_agent.scheduler.daily_job --copy-file output/<date>/copy.json --image-file output/<date>/post.jpg --publish
```

Note `DRY_RUN=true` in `.env` overrides `--publish` as a safety net (see
README) — if the user expects a real post and nothing happened, check that
first.

## Report back

Summarize: which fragrance/theme was used, a one-line description of the
scene you designed, where the generated assets are, and whether it published
or just dry-ran.
