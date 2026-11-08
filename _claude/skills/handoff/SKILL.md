---
name: handoff
description: Tiffin box (handoff) - move a long chat into a fresh one with zero lost detail - the user's verbatim words (said files) + the project LEDGER.md + a short note, proven by the check-tiffin agent before the paste line is given. Use when the user says handoff / Tiffin box / move to a new chat, when the context meter says the chat is heavy at a task boundary, and in a new chat told to open a Tiffin box and continue.
argument-hint: "What will the next chat be used for?"
---

Based on Matt Pocock's `handoff` skill (github.com/mattpocock/skills, MIT), rebuilt for long creative and build work, where one lost decision costs a redo. Nickname: **Tiffin box** (a stacked lunch box: several layers, carried whole).

**Chain rule:** the ledger and the said files belong to the PROJECT and accumulate; only the note is per chat. Chat 10 reads the same ledger chats 1-9 wrote, plus all 9 said files. Nothing is re-summarised, so nothing thins out.

| Layer | What | Who writes it | Can it forget? |
|---|---|---|---|
| **Said file** | every message the user typed in each chat, verbatim, timestamped; one file per chat, all kept | `user_said.py` (script) | no |
| **Claude-said file** | every reply Claude wrote, verbatim (`<said>.claude.md`, same script): the WHY behind choices, dead ends tried | `user_said.py` (script) | no |
| **LEDGER.md** | one line per decision, written the moment it happens | Claude, during the chat (the `ledger_nudge` hook reminds) | only if the chat skipped it; the checker catches that |
| **Note** | goal, state, next steps, traps, pointers | Claude, at pack time | yes, but it only points; the layers above hold the detail |

Tools: `_workflow/tiffin/` (`user_said.py`, `ledger_check.py`, `ledger_brief.py`, `LEDGER-TEMPLATE.md`). Checker: agent `check-tiffin` (`_claude/agents/check-tiffin.md`). Ledger: `<project>/docs/LEDGER.md`; for workspace-wide work, `_workflow/LEDGER.md`.

**Memory mode (chosen once, when the project starts):** how much a new chat reads from the ledger. When you create a project's ledger, ask the user the memory-mode question in `_workflow/tiffin/LEDGER-TEMPLATE.md` (three options with the school-notebook example) and ALWAYS give the picture link with it (`docs/readme/s11-memory-light.svg`, also in this repo on GitHub), because the options are hard to picture from words alone, write the answer as the `Memory mode:` line in the ledger header, and the Tiffin box follows it from then on (no answer = `full`). Proof behind the options: `_workflow/docs/check/RECALL-TEST-2026-11-08.md` (full 12/12, rules 10/12 without searching, lookup 3/12 alone, 12/12 when it searched). The user can switch later by editing that one line.

## A. Packing (old chat)

1. **Dump the words:** `python _workflow/tiffin/user_said.py --current` → `_claude/handoffs/said/<date>_<sid>.md` (user) and `<date>_<sid>.claude.md` (Claude's replies). Add the file to the ledger's **Chats** list. Done when the script prints the path and the ledger lists every chat of the project so far.
2. **Close the ledger:** open the ledger (create it from the template if missing). Walk the said file from the end; every approve / reject / correction / number / preference / named file / open question that is not yet a ledger line gets one now, in the user's words in quotes. Then walk YOUR replies (the `.claude.md` file): every choice you made between options gets a CLAUDE-RULE line with BECAUSE and the dropped options. `ledger_check.py <said> <ledger> [<note>]` lists candidate gaps mechanically. Done when the ledger has no gap you can see on either side. Then mark every older PENDING / OPEN line that this chat finished: change only its status field (after the last `|`) to `DONE (closed chat N: <why>)`; never edit the rest of the line. Unsure = leave it open.
3. **Write the note** `_claude/handoffs/<yyyy-mm-dd-HHMM>_<slug>.md`, under ~80 lines, sections:
   1. **Goal** - the user's words, and what "done" looks like.
   2. **Where it stands** - verified / built but **(not verified)** / not started. State as fact only what you checked.
   3. **Pointers** - ledger path, ALL said-file paths of the project (from the ledger's Chats list), project folder, outputs, skill lessons. Content stays in the files.
   4. **Next steps** - numbered, the very next action first.
   5. **Traps** - what went wrong in this chat.
   6. **Skills to load.**
   Redact secrets. Done when the file exists.
4. **Prove it:** spawn `check-tiffin` mode **pack** with the project folder, EVERY said file in the ledger's Chats list, the ledger and the note. On **FAIL**, paste its LOST lines into the ledger (and fix the note if it invented anything), then run it again. Done when the verdict is **PASS**.
5. **Log and hand over:** `python _workflow/gw.py note "handoff: <slug>"`. Give the user one line:
   `Read _claude/handoffs/<file>.md and continue.` and say: new chat, same folder.

Done when the said file, a PASS from check-tiffin, the logged note and the paste line all exist.

## B. Unpacking (new chat)

1. Read the note. Then read the ledger the way the project chose: `python _workflow/tiffin/ledger_brief.py <ledger>` prints it by the ledger's **Memory mode** line (`full` = the whole ledger, the default; `rules` = open lines + last 2 chats + every old rule/rejection/correction; `lookup` = open lines + last 2 chats). Every open line is work. In `rules` or `lookup` mode, grep the full ledger before deciding anything about an older topic (the output prints the grep line), then the said files: the newest in full, older ones at least their last 15 messages; then the newest `.claude.md` (skim the headings, read the blocks around every PENDING item: they hold the dead ends already tried). All are listed in the ledger's Chats section; grep them whenever a detail is in doubt. Load the skills the note names. Done when all three layers are read.
2. Spawn `check-tiffin` mode **unpack**. Fix nothing yet; take its 10-line state and findings. Done when you have them.
3. Say the state back to the user in one line (what is done, what is not verified, next step 1). Re-check anything "(not verified)" before building on it. Then start next step 1. Open the old chat's fair copy (`_claude/chats/`) only for something all three layers lack, and read only that part: fair copies cut Claude's text to 700 characters, so for Claude's full findings read the files it wrote, or the session `.jsonl`.

Done when the user has the one-line read-back and next step 1 is under way.

## When to pack

- **One chat per task**, not one per step. Pack when the context meter (`context_meter` hook) says heavy (150k soft, 350k strong) **and** a step just finished, or when the user asks.
- Pack at a step boundary: let a long run, a review or a choice round finish, ledger its result, then pack.
