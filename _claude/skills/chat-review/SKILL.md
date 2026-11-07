---
name: chat-review
description: Chat review ("Bigg Boss") - audit past Claude Code sessions on a topic for mistakes the user corrected, prove which repeat across sessions, propose fixes to skills, rules, tools or agents, and apply only the approved ones. Use when the user says "Bigg Boss", asks to review or learn from past chats (session retro, repeated mistakes, improve the system from conversations), or names sessions to review.
---

# Chat review ("Bigg Boss")

**Nickname: Bigg Boss**, after the reality show where cameras watch the whole house and every weekend the host replays the week's mistakes. Same here: every chat is recorded; this skill replays the corrections and fixes the rules so they stay fixed. Files and scripts keep plain names; the nickname is only a trigger. The report is the **Progress card**.

Evidence first, then patterns, then fixes. Edit a skill only from evidence in a timeline.

## 1. Pick the sessions
- The user names a topic or chat titles. List sessions with `mcp__ccd_session_mgmt__list_sessions` (include_archived) and match titles, or search the fair-copy index `_claude/chats/CHATS-*.md`.
- Map each app session to its transcript: `~/.claude/projects/<cwd-slug>/<cli-id>.jsonl`. The ids differ; match by **last activity time** (the transcript's last `"timestamp"` equals the session's `lastActivityAt`). `btw:` side sessions are forks: include them only when the user asks.
- Show the user the list (title, date, size) before reading if there is any doubt.

Done when every chosen session has its transcript path (and, if there was doubt, the user has OKed the list).

## 2. Clean each transcript
```
python Common/tools/chat-review/chat_to_timeline.py <cli-id or path> <scratchpad>/<key>.md
```
Output: numbered user turns `U1..Un` (full text), Claude's text (trimmed), one line per tool call; tool output and system noise are dropped. Write it to the scratchpad, outside the repo.
Messages typed while Claude is busy are stored as `queue-operation` entries; the cleaner includes them (many corrections live there). Messages from other sessions appear as `(message from session '…')`.

Done when every chosen session has its `<key>.md` timeline in the scratchpad.

## 3. Extract corrections (one reader agent per session, in parallel, read-only)
Each agent reads its whole timeline and writes `<key>.findings.md`:
- **Corrections**: U-number, time, category, exact user quote (≤30 words), what Claude had done, root cause (`rule missing` | `rule existed but ignored` | `skill/kit gave wrong method` | `no self-check caught it` | `misread the request` | `tool/env limit`), repeat-within-session, fixed-or-not.
- **Approvals**: methods the user confirmed ("perfect", "lock it"); these are keepers.
Prompt template: `references/extract-prompt.md`.

Done when every session has its `<key>.findings.md`.

## 4. Cluster into patterns (yourself, not an agent)
- Merge corrections across sessions into patterns. **A pattern needs ≥2 corrections in ≥2 sessions**, or ≥3 in one. Everything else is a one-off: list it in one line, with no fix.
- For each pattern, check the current system: grep `~/.claude/working-style.md`, `~/.claude/CLAUDE.md`, the project's `CLAUDE.md` and the skill that owns the task. Mark:
  - **not written anywhere** → add a rule;
  - **written but ignored** → propose a *check* instead of more words (script, checklist step, hook, reviewer agent);
  - **written wrong / conflicting** → rewrite or delete the old rule;
  - **needs a tool** → propose the tool and where it lives (`Common/tools/...`);
  - **already fixed** (a rule or tool was added in the session itself) → list it as "watch", outside the proposals; escalate only if it shows up again in a LATER session.
- Verify every claim against the timeline (open the U-turn) before it goes in the report.
- Experience: most single-session lessons are already saved in-session; the real value is the cross-session patterns with no rule at all, and rules that exist but keep being skipped.

Done when every pattern has one of the five marks and every claim's U-turn has been opened.

## 5. Progress card (short; the user may read it on a phone)
Table: `# | Pattern | Times / sessions | Proof (quotes + U refs) | Why it happened | Proposed fix → target file`.
Then: one-offs (one line each), approvals worth locking. Save to `_claude/chats/reviews/<yyyy-mm>-<topic>/REPORT.md`, titled "Progress card".
Done when that REPORT.md exists with the table, one-offs and approvals.

## 6. Apply only what the user ticks
- Edit only the ticked targets. Preferences → `working-style.md`; workspace rules → `CLAUDE.md`; a task's method → the skill that owns it; a reusable check → a script in `Common/tools/` that the skill points to.
- For a rule that was "written but ignored", prefer a check that runs automatically.
- Log: `python _workflow/gw.py note "chat-review: <what changed and why>"`.

Done when every ticked target is edited, only those, and the note is logged.
