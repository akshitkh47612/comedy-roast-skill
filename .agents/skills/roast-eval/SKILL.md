---
name: roast-eval
description: >
  Generate a comedy roast of the user (same material sources and structure as
  comedy-roast: WorkIQ, GitHub, X/Twitter) and calibrate it against the
  user's own taste over time. Every joke gets a Pass/Fail/TooFar rating
  through a small review app; ratings build a personal taste profile and a
  self-critique judge that filters future jokes before delivery. USE FOR:
  roast me, comedy roast, roast my week, calibrated roast, roast (with
  learning/feedback), improve my roast.
---

# Roast + Eval Skill

This is `comedy-roast` plus a feedback loop borrowed from the `error-discovery`,
`write-judge-prompt`, and `validate-evaluator` skills in evals-skills: instead of
generating the same kind of roast forever, every joke gets rated, ratings become
a taste profile, and the taste profile becomes a judge that filters future drafts.

This file covers phases 1 through 3: gather material, draft and self-filter jokes,
deliver the roast, and launch the review app. Once the app is running and the
human starts rating, follow [review-loop.md](review-loop.md). Once enough new
ratings have accumulated, that file will tell you to follow
[calibrate.md](calibrate.md).

## State files (in `data/`, created on first run, never committed — see `.gitignore`)

- `bits.jsonl` — one line per joke ever drafted: `{id, roast_id, timestamp, section, text, source_refs, label, note}`. `label` is `null` until rated, then `"Pass"`, `"Fail"`, or `"TooFar"`.
- `taste_profile.json` — `{avoid_topics: [], favorite_angles: [], edginess: 1-5, running_pass_rate, last_updated}`.
- `judge_prompt.md` — the current versioned Pass/Fail judge (absent until the first calibration).
- `judge_stats.json` — `[{version, trained_on_n, tpr, tnr, calibrated_at}, ...]`.

If `data/` or any file in it doesn't exist yet, this is the first run: skip the
judge filter in Step 3, and initialize `taste_profile.json` with empty/neutral
defaults (`avoid_topics: []`, `favorite_angles: []`, `edginess: 3`).

## Step 1: Gather the Material

Identical to `comedy-roast`'s Step 1 — collect activity from all three sources
in parallel, don't skip any:

- **WorkIQ**: use `WorkIQ-ask_work_iq` for meetings, emails, files edited in the
  last 7 days. Look for meetings-that-could-be-emails, suspicious calendar
  gaps/overload, documents nobody asked for.
- **GitHub**: get the username, then `search_pull_requests` /
  `search_issues` with `author:USERNAME created:>YYYY-MM-DD` (7 days ago), and
  `list_commits` on active repos. Look for tiny PRs with huge descriptions,
  2 AM commits, self-merged PRs, "fix typo" chains.
- **X/Twitter**: `getUsersMe`, then `getUsersPosts`, `getUsersLikedPosts`,
  `getTrendsPersonalizedTrends`. Look for hot takes with zero engagement,
  posting frequency, liking their employer's tweets.

If a source errors or isn't connected, skip it and note that in the delivered
roast (same fallback lines as `comedy-roast`: e.g. "even Microsoft 365 has
blocked you"). Always produce a roast even with partial data.

## Step 2: Draft Candidate Bits

Write **more jokes than you need** — about 1.5x. For a typical ~13-joke roast
(2-3 per section across Opening / Work / Code / Timeline / CrossRef / Closer),
draft ~20 candidates. Each candidate is a discrete bit:

```json
{"id": "b17", "section": "Code", "text": "...", "source_refs": ["PR #482"]}
```

Cross-reference across sources for the CrossRef section (contradictions
between what they said publicly and what they actually did — see
`comedy-roast`'s Step 2 for the pattern). Apply the same tone rules: specific,
clever, affectionate, punch up at habits not down at the person, use real
numbers.

If `taste_profile.json` has `favorite_angles`, bias drafting toward those
angles. Do not draft anything touching `avoid_topics` — cheaper to avoid it
now than filter it out next.

## Step 3: Self-Filter

1. **Hard filter.** Drop any candidate that touches an `avoid_topics` entry
   even if it slipped through drafting.
2. **Judge filter** — only if `judge_prompt.md` exists (skip entirely on the
   first-ever run, there's nothing to calibrate against yet). Score every
   remaining candidate with the judge: `{critique, result: Pass|Fail}`. Keep
   all Pass bits. For any section that now has fewer than 2 surviving bits,
   redraft **one retry** for that section using the Fail critiques as
   feedback, then judge the retry once — don't loop indefinitely. If still
   short after the retry, deliver with fewer jokes in that section rather than
   forcing a bad one through.

Log **every** candidate bit (Pass, Fail, and hard-filtered) to `bits.jsonl`
with `label: null` — ratings come later, from the human, in Step 5.

## Step 4: Assemble and Deliver

Structure the surviving bits into the roast monologue: Opening → Work Roast →
Code Roast → Timeline Roast → Cross-Reference Special → Closer, same shape as
`comedy-roast`. Deliver it in chat as the final answer to "roast me."

## Step 5: Launch the Review App

Tell the user what you're doing before you do it: "Building the review app so
you can rate which jokes actually landed."

1. `app/server.py` and `app/index.html` are static — nothing to regenerate.
   Just start the server, pointed at this roast's `data/bits.jsonl`:
   `python3 .agents/skills/roast-eval/app/server.py` (default port 8420; pick
   another free port if it's taken and say so).
2. Open it in the browser (or tell the user the URL if you can't open browsers
   directly).
3. Tell the user the app is ready, and explain the interaction in one line:
   "Rate each joke 👍 Landed / 👎 Bombed / 🚩 Too far, add a note if you want,
   it autosaves."
4. Hand off to [review-loop.md](review-loop.md) to monitor ratings as they
   come in.

If this is a non-interactive run (no human available to rate, e.g. `claude
-p`), build and smoke-test the app, then stop the server and give the launch
command for later. Never claim ratings happened or the server is still
running when it isn't.
