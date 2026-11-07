---
name: working-style
description: Working style - the user's personal profile of preferences. Use at the start of every task (read it), whenever the user corrects, rejects, approves or states a preference (record it), and when they ask to learn, update or show their style.
---

# Working style — learn it, use it

Profile file (one for all projects): `~/.claude/working-style.md`. It is a link to `_claude/home/working-style.md` in your workflow repo, so both paths are the same file and it syncs between machines.

## At the start of a task
Read the profile. Follow every rule in it without being reminded. If a rule conflicts with the request, the request wins for this task only. Done when the profile is read in full.

## While working — what counts as a signal
- **Correction:** "no", "not like that", "remove that", "stop doing X" → strongest signal.
- **Rejection:** the user throws away a design, edit or approach → record what was rejected and why (ask "which part?" if unclear).
- **Approval:** "perfect", "this is good", "keep this" → record what worked, so it gets repeated.
- **Repeated choice:** the user picks the same option 2+ times (same model, font, tone, format) → record it as a default.

## Recording
Edit the profile right away, at the moment of the signal:
- One line per rule, under the right heading. Short and concrete: "Captions: bold, 2–3 words per line, centred lower third", rather than "likes good captions".
- Add the date: `(yyyy-mm-dd)`. When the rule comes from a chat, also keep the user's exact words in the project ledger (`docs/LEDGER.md`): the profile line is the reading, the ledger holds the quote.
- When a new rule contradicts an old one, **replace** the old one, so only the newest stays.
- Record what will matter next time; one-off details about a single file or task stay in that project.
- Store only the user's working preferences; passwords, keys and other people's private data stay out.
- Tell the user in one short line: `Noted in your style: <rule>`.

Done when the dated line is in the profile and the user has the `Noted` line.

## Review
When the user says "show my style", print the profile. When it passes ~80 lines, merge duplicates and drop stale lines.
