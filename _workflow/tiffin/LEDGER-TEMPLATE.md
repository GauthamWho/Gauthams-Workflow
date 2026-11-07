# LEDGER - <project name>

The project's memory. One line per thing the user decided, written THE MOMENT it happens (not at the end of the chat).
A new chat reads this first; a Tiffin box only points here. Append only; never rewrite old lines (strike through with `~~` if reversed).

Line format:
`- [yyyy-mm-dd HH:MM] KIND - "<user's words, up to 15>" -> <what changed, which file / version> | APPLIED or PENDING`

KIND is one of: APPROVED, REJECTED, CORRECTED, NUMBER (any threshold, size, length, count), PREF (taste that stays true), FILE (a path the user named), OPEN (asked, not yet answered), **CLAUDE-RULE** (a number or rule Claude or a reviewer chose, which the user did not say - never written in the user's voice). A CLAUDE-RULE line ALWAYS carries its reason and the options it beat: `-> <choice> BECAUSE <reason>; tried and dropped: <a>, <b>`. Without the reason the next chat repeats the dead ends.

Rules
- The user's words go in quotes, verbatim. Your reading of them goes after the arrow.
- Every choice YOU make between options (a position, a colour, a method, a tool) gets a CLAUDE-RULE line the same turn, with BECAUSE and the dropped options. Your full replies are kept in `_claude/handoffs/said/<file>.claude.md` by the same script that keeps the user's words.
- A lasting preference ALSO goes to `~/.claude/working-style.md` (or the skill that owns it); the ledger line then says `-> working-style`.
- PENDING lines are the first thing the next chat does. When one is finished, change ONLY its status field (after the last `|`) to `DONE (closed chat N: <why>)`; the rest of the line is never edited. A new chat reads `ledger_brief.py` (open lines + the last 2 chats), not the whole file, so closing lines keeps every new chat light.
- The ledger is per PROJECT, never per chat: chat 3 reads the same file chats 1 and 2 wrote. Nothing is re-summarised, so nothing thins out across handoffs.
- `python _workflow/tiffin/ledger_check.py <said.md> <this file> [note.md] --project <project>` compares this file with what the user actually said (said file) and lists gaps.

## Chats (every chat of this project, oldest first - the said file holds the user's words verbatim)

- <yyyy-mm-dd> <chat name> -> `_claude/handoffs/said/<file>.md`

## Decisions

- [yyyy-mm-dd HH:MM] FILE - "example line, delete me" -> docs/PLAN.md | APPLIED

## Open questions (the user has not answered yet)

- none
