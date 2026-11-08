# Global rules ({{WORKFLOW}}, all projects)

Claude Code loads this file in every project. Follow it without being told.
Paths below are relative to the {{WORKFLOW}} folder (the repo root); on any machine it is `$GW_HOME`. Code gets paths from `Common/tools/gwpaths.py`, never a hard-coded drive.

## Start of every task
1. **Working style:** read `~/.claude/working-style.md` and follow it. When {{NAME}} corrects, rejects, approves or states a preference, add a line to that file the same turn (skill `working-style`): date + their words in quotes.
2. **Skills from GitHub:** at the start of a new project or a new kind of task, run `skill-installer` first: check installed skills, find the best missing ones on GitHub, install them, then do the work with them.

## Folder layout
| Folder | What goes here |
|---|---|
| `_claude/skills/` | Skills (linked into `~/.claude/skills`, so every project gets them). |
| `_claude/agents/` | Agents: `check-tiffin`, `check-progress`, `premium-critic`. |
| `_claude/home/` | This file and the `working-style.md` form. |
| `_claude/handoffs/said/` | Said files: {{NAME}}'s words and Claude's replies per chat, verbatim. |
| `_workflow/` | `gw.py` (sync), `LEDGER.md`, `tiffin/` (ledger template + checks), `hooks/`. |
| `Common/tools/` | Shared tools: `lan/` (phone links, copy bar), `chat-review/` (Bigg Boss, token use), `gwpaths.py`. |
| `install/` | The installer (fills `{{NAME}}` / `{{WORKFLOW}}` from `_workflow/me.json`). |

Anything a second project needs moves to `Common/` (one copy) and is imported from there.

## Starting work: Matt Pocock's flow (every project, sub-project, app or feature)
Matt Pocock's skills (github.com/mattpocock/skills) are part of every plan. Many start only from a slash command; when a step below is reached, open `~/.claude/skills/<name>/SKILL.md` and follow it directly. His `/code-review` is installed as `mp-code-review`; his `/handoff` is our **Tiffin box**.
1. **Grill first.** Before any plan or build, interview {{NAME}} with `grilling` (in a project folder: `grill-with-docs`, which keeps `GLOSSARY.md` + decisions in `docs/`). Plain words, one question at a time; design questions stay visual (pickers). Done when every open question is settled.
   **First question of every new project: the Memory mode** (how much a new chat reads from the project notes): Whole notebook (default) / Short notes + rules / Short notes + look-up. Ask {{NAME}} with the question in `_workflow/tiffin/LEDGER-TEMPLATE.md` and write the answer in the project LEDGER header; the Tiffin box follows it (skill `handoff`).
2. **Big and foggy** (new app, new pipeline) → `wayfinder`, then `to-spec`.
3. **More than one chat of work** → `to-spec` → `to-tickets`, then `implement` one ticket per fresh chat. Creative pieces that need one continuous run of taste (one film, one design) stay in one chat: grill → the piece's own steps → retro.
4. **Needs a runnable answer** (a look, a mechanic) → `prototype`; findings go into a file in `docs/`, the LEDGER points to it.
5. **Hard bug** → `diagnosing-bugs`. **Research** → `research` (findings saved to a file). **Code** → `tdd`, then `mp-code-review`.
6. **End of a build** → `retro`: what to change in skills, rules, checks or agents; feeds Bigg Boss and `working-style.md`.
7. **Writing or training any skill, agent or CLAUDE.md** → `writing-for-agents` (short always-loaded lines, details behind pointers, wanted behaviour said positively, one source of truth).

**Offer the next step by name** in one line with the phrase to say, e.g. "Pack the Tiffin {{NAME}}: say **Tiffin box**." / "Call Bigg Boss {{NAME}}: this mistake came back; say **Bigg Boss on <topic>**."

## Chat size, LEDGER and Tiffin box
Every reply re-reads the whole chat, and very long chats lose quality.
- **One task per chat.** Start a new chat for a new app or an unrelated job; otherwise only when the **Auto meter** hook says the chat is heavy **and** a step just finished. Then pack a **Tiffin box** (skill `handoff`).
- **Write the project LEDGER as you go** (`<project>/docs/LEDGER.md`, template `_workflow/tiffin/LEDGER-TEMPLATE.md`): the moment {{NAME}} approves, rejects, corrects, gives a number or a preference, append one line with their words in quotes. The `ledger_nudge` hook reminds you; a new chat reads the ledger first.
- **Your own choices too:** when you pick between options (position, colour, method, tool), append a `CLAUDE-RULE` line the same turn with `BECAUSE` and the options you dropped, so the next chat keeps the why and never repeats a dead end.
- **A Tiffin box is three layers:** the said file (`_workflow/tiffin/user_said.py` writes both sides verbatim), the LEDGER, and a short note. The `check-tiffin` agent must say PASS (nothing lost, nothing invented) before the paste line is given, and runs again in the new chat before any build.
- **Continue a chat on another machine:** open a new chat in the same folder and say "continue <chat title>"; read the project LEDGER and the chat's said file first.
- Heavy reading (many files, logs, research) goes to subagents, so only their short answer enters the chat.
- **Is it working?** After 2 fix rounds on the same problem, or a "worse" verdict, run `check-progress` before another round or ETA.
- **Premium check:** after building or changing any page, app or video, run `premium-critic` and fix what it finds before {{NAME}} sees it.

## Learnings go into the skills
{{NAME}} runs several chats at once and forgets later what was learned where, so every lesson goes the same day into the skill or doc that owns it:
1. **Preference** → `~/.claude/working-style.md`.
2. **Method** → the skill that owns it; a tool a second project could use → `Common/` with the skill pointing at it.
3. **Log it:** `python _workflow/gw.py note "learned: <what> (from <project>)"`.
Auto-memory and skill "Lessons" are readings, never the only copy: each cites the LEDGER line or said file behind it. At the end of a session, say whether any lesson still has no home.

## GitHub sync (one private repo, automatic)
The {{WORKFLOW}} folder is one private GitHub repo holding skills, rules, memory, tools and projects; media stays out (`.gitignore`).
- **Sync is automatic** (hooks: pull at session start, checkpoint push, push at session end). **Never ask "push?".** "Push now" = `python _workflow/gw.py push`.
- **While working,** log the *why* of each change: `python _workflow/gw.py note "<what and why>"`. It becomes the commit message.
- **Guard** (pre-commit) blocks secrets, files over 20 MB, media/model files and nested repos: fix the cause (add to `.gitignore`); never bypass it.
- **Conflict:** both versions are kept; show {{NAME}} both, merge with their choice, commit, `gw.py push`. Never force-push.
- When a tool is upgraded, update `_workflow/TOOLS.md` + `requirements-gw.txt`.

## Every local page opens on the phone too (automatic, never ask)
Details and gotchas: `Common/tools/lan/README.md`.
- **Static pages** (pickers, reports, previews): `python Common/tools/lan/serve.py <folder> <port>` (Wi-Fi, video seeking, no-cache). To send a video: `share_video.py <mp4>`.
- **Dev servers:** start them with host `0.0.0.0`. Ports 3000-5999 or 8000-8999 (on Windows, `ALLOW_PHONE_ONCE.ps1` opens them to the home Wi-Fi once).
- **Phone check before every phone link:** `python Common/tools/lan/phonecheck.py <port> [path]`. PASS → give both links it prints (`localhost` and the Wi-Fi address). FAIL → give the PC link only, say why, and give a double-click launcher.
- **Picker pages:** the copy line sits in a sticky bar at the TOP with a Copy button (`python Common/tools/lan/add_copybar.py <page.html>`). Every pick toggles off on a second tap, "select all" comes with **Clear all**, and every item has its own note box that goes into the copy line.
- Pages work at 375 px phone width (`playsinline`, `play()` inside the tap).
