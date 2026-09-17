# 🔥 Comedy Roast Skill

Agent skills that roast you based on what you *actually* did last week — pulling material from your GitHub activity, X/Twitter posts, and Microsoft 365 work data.

Every joke is grounded in real data: your commits, your meetings, your tweets. No generic punchlines. The best roasts come from cross-referencing what you said publicly versus what you actually worked on.

This repo has two skills:

| Skill | What it does |
|-------|---------------|
| [`comedy-roast`](.agents/skills/comedy-roast/SKILL.md) | The original, one-shot roast. Same material, same structure, every time. |
| [`roast-eval`](.agents/skills/roast-eval/SKILL.md) | `comedy-roast` plus a feedback loop: rate each joke, and the roast gets calibrated to your taste over time. Start here unless you specifically want the stateless version. |

## How it works (both skills)

When you ask your coding agent to "roast me," the skill:

1. **Gathers material** from three data sources in parallel:
   - **GitHub** — PRs, commits, issues (tiny PRs with huge descriptions, 2 AM commits, self-merges…)
   - **X (Twitter)** — posts, likes, trends (hot takes with zero engagement, ratio'd posts…)
   - **WorkIQ (Microsoft 365)** — meetings, emails, files (meetings that could have been emails…)
2. **Cross-references** for contradictions (tweeted "deep work day 🔥" but GitHub shows zero commits)
3. **Delivers a full roast monologue** — opener, work roast, code roast, timeline roast, and a backhanded compliment to close

`roast-eval` also drafts more jokes than it delivers, self-filters them against a personal taste profile, and opens a small local review app so you can rate what actually landed.

## `roast-eval`: a roast that learns your taste

`roast-eval` treats every joke as a labeled example, the same way an eval pipeline treats traces:

- Every joke gets logged (`Pass` / `Fail` / `TooFar`, plus an optional note) through a zero-dependency local review app the skill opens for you.
- Ratings roll up into a **taste profile** — topics to avoid, angles that land, your running pass rate — read fresh on every future roast.
- Once you've rated enough jokes, the skill calibrates a personal **LLM judge** (few-shot examples pulled from your own ratings, measured with TPR/TNR like a real eval) and uses it to pre-filter draft jokes before you ever see them.
- Nothing is graded on a fixed scale — Pass/Fail only, per the same reasoning product evals use: binary judgments are calibratable, 1-5 scores aren't.

All of your rating history and taste profile stay on your machine (`.agents/skills/roast-eval/data/`, git-ignored) — never committed, never sent anywhere except the LLM calls the skill itself makes.

See [`.agents/skills/roast-eval/SKILL.md`](.agents/skills/roast-eval/SKILL.md), [`review-loop.md`](.agents/skills/roast-eval/review-loop.md), and [`calibrate.md`](.agents/skills/roast-eval/calibrate.md) for the full mechanics.

## Installation

Install with the [`skills`](https://www.npmjs.com/package/skills) CLI. Grab both skills:

```sh
npx skills add akshitkh47612/comedy-roast-skill
```

Or install just one:

```sh
npx skills add akshitkh47612/comedy-roast-skill --skill roast-eval
npx skills add akshitkh47612/comedy-roast-skill --skill comedy-roast
```

No `skills` CLI, or want it in your agent's global skills directory directly? Clone the repo and copy the folder:

```sh
git clone https://github.com/akshitkh47612/comedy-roast-skill.git
mkdir -p ~/.claude/skills
cp -r comedy-roast-skill/.agents/skills/roast-eval ~/.claude/skills/roast-eval
```

(Claude Code reads skills from `~/.claude/skills/<name>/SKILL.md`; other agents that follow the same `SKILL.md` convention can point at the same folder.)

## Required MCP Servers

This skill queries three MCP servers for roast material. You'll need to have them connected to your agent:

| Source | MCP Server | What It Provides |
|--------|-----------|-----------------|
| GitHub | [github/github-mcp-server](https://github.com/github/github-mcp-server) | Commits, PRs, issues |
| X (Twitter) | [xdevplatform/xmcp](https://github.com/xdevplatform/xmcp) | Posts, likes, trends |
| Work IQ (Microsoft 365) | [microsoft/work-iq](https://github.com/microsoft/work-iq) | Emails, meetings, files |

> **Note:** The skill gracefully handles missing sources. If a server isn't connected, it roasts the silence instead. You don't need all three — even just GitHub is enough to get a roast.

## Usage

Once installed, just ask your coding agent:

- "roast me"
- "roast my week"
- "give me a comedy roast"
- "calibrated roast" / "roast me and learn from it" (nudges toward `roast-eval` if both skills are installed)

With `roast-eval`, after the roast is delivered your agent opens a review app (default `http://127.0.0.1:8420`) — rate each joke 👍/👎/🚩, optionally say why, and it autosaves. Do this a few times and later roasts start reflecting what actually made you laugh.

## Example

> *"You mass-produced 47 meetings this week and then sent an email about 'protecting focus time.' Your GitHub was so quiet I thought you'd been laid off — until I saw you mass-liking tweets about productivity at 11 PM. But hey, at least your one PR description was longer than your actual code. That takes commitment."*
