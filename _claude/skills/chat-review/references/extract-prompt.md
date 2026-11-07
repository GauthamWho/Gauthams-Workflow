# Reader-agent prompt (one per session)

Fill `{title}`, `{timeline}`, `{jsonl}`, `{out}`. Run all sessions in parallel, read-only.

```
You are auditing ONE past Claude Code session between the user and Claude.
Goal: find every place Claude made a mistake that the user had to correct. Evidence only, no fixes.

Session: {title}
Cleaned timeline (read ALL of it, in chunks, start to end): {timeline}
Format: "### U<n> [time]" = user turn; "**A:**" = Claude's text (trimmed); "- `Tool` ..." = tool calls.
Raw transcript (huge; only grep it for a specific phrase): {jsonl}

The user may type by voice, so wording can be rough. A correction is any user turn that rejects or criticises
output, repeats an instruction already given, points out something missed/broken/ugly/out of sync, redirects the
approach, or shows frustration. Also note approvals ("this is good", "perfect", "lock it").

Write to {out}:

## Corrections
- **C<k> — U<n> [time]** — category (visual-quality, timing/sync, sound, text/typography, layout,
  process/workflow, communication, asked-too-much, didnt-ask, ignored-existing-rule,
  tool/env, speed, misunderstood-request, other)
  - User said: "<exact quote, max 30 words>"
  - What Claude had done: <1-2 concrete lines>
  - Likely root cause: [rule missing | rule existed but ignored | skill/kit gave wrong method |
    no self-check caught it | misread the request | tool/env limit] + 1 line why
  - Repeat? <yes: earlier at U<m> | no>
  - Fixed in session? <yes, how | no>

## Approvals (methods that worked)
- U<n>: "<quote>" — what was approved

## Session summary
3-5 bullets: the biggest recurring frictions, with counts.

Be strict: only real corrections, quote exactly, cite U numbers.
Reply with just the counts and the 3 biggest frictions.
```
