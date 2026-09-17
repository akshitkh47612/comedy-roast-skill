# Review Loop

The app is running and the human is rating jokes. You are an active participant,
same spirit as `error-discovery`'s review loop, adapted for a small per-roast
batch instead of an open-ended dataset.

## Progress updates

Say what you're doing at each step. Don't go silent while the human rates —
when you notice new ratings, say what came in. When you fold ratings into the
taste profile, say what changed ("adding 'crypto tweets' to avoid_topics — that's
0 for 4 now").

## Monitor for ratings

Watch `data/bits.jsonl` for rated bits (`label` no longer `null`) by comparing
content every 2 seconds.

- Claude Code: use the Monitor tool with `persistent: true` — each detected
  change becomes a notification.
- Otherwise: poll with a simple read-compare loop. Do not use filesystem
  events (`inotifywait` etc.) — polling is cross-platform reliable.

## Fold ratings into the taste profile

Whenever new ratings arrive:

1. Read all rated bits for this `roast_id` (and, for context, the running
   history across all roasts).
2. Update `taste_profile.json`:
   - Any `TooFar` bit's topic → add to `avoid_topics` (dedupe against what's
     already there).
   - Sections/topics with a high Pass rate across roasts → add or reinforce
     an entry in `favorite_angles`.
   - Recompute `running_pass_rate` = Pass / (Pass + Fail + TooFar) across all
     rated bits ever.
   - Bump `last_updated`.
3. If a bit has a free-text note, read it — notes are the highest-signal input
   (same principle as error-discovery: "the human notices, the agent
   organizes"). A note like "the PR joke would've landed if it named the repo"
   should sharpen `favorite_angles` or a future redraft, not just the binary
   label.
4. Write the updated `taste_profile.json`.

## When to recalibrate

Track two counts: `total_labeled` (all-time rated bits in `bits.jsonl`) and
`new_since_calibration` (rated bits added since `judge_stats.json`'s last
entry, or all of them if `judge_stats.json` doesn't exist yet).

Trigger [calibrate.md](calibrate.md) when **both**:
- `new_since_calibration >= 10`
- `total_labeled >= 20` AND at least 5 bits in each class (Pass vs Fail+TooFar
  combined)

Tell the user before triggering it: "You've rated 22 jokes total, 11 since the
last calibration — recalibrating the judge now." If the thresholds aren't met
yet, just keep monitoring; there's nothing to do.

## Closing out a session

Once the human stops rating (no new ratings for a while, or they say they're
done), stop the server, report a quick summary (bits delivered / rated /
Pass rate this roast, and current `avoid_topics` + `favorite_angles`), and
stop. Don't leave the server running unattended.
