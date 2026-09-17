# Calibrate the Judge

Scaled-down `write-judge-prompt` + `validate-evaluator`, run against one
person's growing joke history instead of a product's traces. Triggered by
[review-loop.md](review-loop.md) once there's enough new signal.

The full evals-skills discipline (10-20% train / 40-45% dev / 40-45% test,
100+ labeled examples, TPR/TNR ≥ 90%) assumes a product eval with a labeling
budget. This is one person rating their own jokes — the same math would
demand months of roasts before producing a single judge. Everything below is
the same shape, deliberately shrunk: skip the fixed test set until there's
enough data for it to mean anything, and treat this as a *personal* filter
that improves gradually, not a shippable evaluator.

## Step 1: Build the labeled set

Read all rated bits from `bits.jsonl` (label != null). Map `Fail` and `TooFar`
both to the negative class for judge purposes — the judge stays strictly
binary Pass/Fail per `write-judge-prompt`'s anti-Likert rule. (`TooFar` is
still tracked separately in `taste_profile.json`'s `avoid_topics` — that's a
hard filter, not something the judge needs to relearn.)

## Step 2: Small-N split

- If `total_labeled < 60`: sort by timestamp, hold out the most recent ~30%
  as **dev** (never used as few-shot, used only to measure this version).
  Everything older is the **few-shot pool**. No separate test set yet — say so
  explicitly in the calibration summary ("N=24, using train/dev only; test
  split kicks in past N=60").
- If `total_labeled >= 60`: switch to the real 3-way split
  (`train_test_split`, stratified, ~15/45/40) like `validate-evaluator`
  describes, and from here on only touch the test set once per calibration
  run, never mid-iteration.

## Step 3: Write `judge_prompt.md`

Four components, same as `write-judge-prompt`:

1. **Criterion**: "You are evaluating whether a specific joke would make
   [person] laugh, based on their actual reactions to past jokes." One
   sentence, this exact framing — not "is this joke good."
2. **Pass/Fail definitions**, drawn from current `taste_profile.json`:
   - PASS: matches a `favorite_angle`, or is specific + cross-referenced +
     affectionate in the way their past Pass-rated jokes were.
   - FAIL: generic, not specific to real activity data, or structurally
     similar to a past Fail/TooFar bit (quote the closest one).
3. **Few-shot examples** from the training split only: pick 2-4, favor
   borderline ones (a Fail that's close to the Pass line, and vice versa) —
   these teach nuance better than obvious cases. Each example needs a written
   critique before its Pass/Fail result, matching the detail level you want
   the judge itself to produce.
4. **Structured output**: `{"critique": "...", "result": "Pass"|"Fail"}`.
   Critique first, verdict second — forces the judge to justify before
   deciding.

Version the file: keep the previous `judge_prompt.md` content in
`judge_stats.json`'s history (or a `judge_prompt.v{N}.md` sibling) rather than
just overwriting silently, so drift is inspectable later.

## Step 4: Measure on dev

Score every dev-split bit with the new judge prompt. Compute:

```
TPR = (judge Pass AND human Pass) / (human Pass)
TNR = (judge Fail AND human Fail) / (human Fail)
```

## Step 5: Iterate once, then accept

- If TPR ≥ 80% and TNR ≥ 80%: accept this version.
- If not: inspect the disagreements (false-Pass → the judge is too lenient,
  strengthen FAIL definitions or add an edge-case example; false-Fail → too
  strict, clarify PASS definitions) and rewrite once. Re-measure. Accept
  whatever comes out of this second pass regardless of the numbers — do not
  loop further. This is a personal-taste judge that gets another shot at the
  next calibration trigger, not a launch gate.
- If `total_labeled >= 60`, also run the accepted version once on the test
  split for the unbiased number to record — and don't iterate after seeing it.

## Step 6: Record stats

Append to `judge_stats.json`:

```json
{"version": 3, "trained_on_n": 24, "tpr": 0.83, "tnr": 0.79, "calibrated_at": "2026-09-17T..."}
```

Tell the user the result in one or two lines: version, TPR/TNR, and what
changed in the prompt this round (e.g. "tightened the FAIL definition around
generic 'you code weird' style jokes after 3 false passes").
