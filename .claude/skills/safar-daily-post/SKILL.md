---
name: safar-daily-post
description: Write and publish today's Safar car-perfume social post (Instagram/Facebook/YouTube) yourself instead of calling an LLM API, then hand off image/video rendering and publishing to the existing Python pipeline. Use when asked to run today's Safar post, generate today's Safar caption, or do the daily Safar content task.
---

# Safar daily post

This repo already has a full pipeline for the Safar car-perfume brand
(`src/safar_agent/`): image composition, video rendering, and posting to
Facebook/Instagram/YouTube. Normally step 2 below (writing the caption) is
done by calling OpenAI or Anthropic's API. This skill has *you* do that step
directly instead — no `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` needed — so the
whole thing runs on the user's existing Claude subscription rather than
metered API billing. Everything mechanical (which fragrance, rendering,
actually posting) still goes through the same deterministic Python code —
don't reimplement or bypass that part.

Run all commands from the repo root, with the venv active
(`source .venv/bin/activate`).

## Step 1 — Get today's brief

```bash
python scripts/print_today_brief.py
```

This prints JSON with today's `fragrance_id`, `fragrance_name`,
`fragrance_tagline`, `scent_notes`, `liquid_color`, `theme_id`,
`theme_category`, `theme_hint`, and `bottle_design`. The `theme_id` is
randomly picked and **must** be echoed back verbatim in step 2 — don't
substitute a different theme even if you think of a better one, since the
history log has already logically reserved it for today.

## Step 2 — Write the copy

Using the brief above, write copy in this brand voice:

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

Write a JSON file at `output/<today's date, YYYY-MM-DD>/copy.json` with
**exactly** this shape (create the directory if needed):

```json
{
  "concept": "one-line visual/creative concept a designer or video editor could act on",
  "instagram_caption": "...",
  "facebook_caption": "...",
  "youtube_short_title": "...",
  "youtube_short_description": "...",
  "on_image_text": "short punchy text to overlay on the graphic, <=8 words",
  "video_narration": "2-3 short spoken sentences for a 15-second vertical video voiceover, punchy and conversational",
  "hashtags": ["#...", "#...", "... 8-12 total, mix of brand + car + fragrance + trending-style tags"],
  "_meta": { "theme_id": "<the theme_id from step 1, unchanged>", "fragrance_id": "<the fragrance_id from step 1, unchanged>" }
}
```

The `_meta` block is required — it's how the pipeline knows which theme you
wrote for, since it doesn't re-run any random selection itself.

## Step 3 — Hand off to the pipeline

Dry run first (always do this unless the user has explicitly confirmed they
want to publish for real):

```bash
python -m safar_agent.scheduler.daily_job --copy-file output/<date>/copy.json
```

Check the generated image/video in `output/<date>/` look right. Only add
`--publish` once the user has confirmed — this posts to real, public
Facebook/Instagram/YouTube accounts, so don't pass it unprompted or by
default:

```bash
python -m safar_agent.scheduler.daily_job --copy-file output/<date>/copy.json --publish
```

Note `DRY_RUN=true` in `.env` overrides `--publish` as a safety net (see
README) — if the user expects a real post and nothing happened, check that
first.

## Report back

Summarize: which fragrance/theme was used, where the generated assets are,
and whether it published or just dry-ran.
