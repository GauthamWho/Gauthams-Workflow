---
name: my-workflow
description: My workflow - the map of your own workspace repo - where things live, automatic GitHub sync, the ledger, Tiffin box handoffs, said files, chat fair copies, PC and Mac paths. Use at the start of any task, when the user says sync / push / pull, sets up a machine, asks where something is, continues a chat from the other machine, or a path in a doc belongs to the other machine.
---

# Your workflow: the whole workspace

One private GitHub repo holds the knowledge of your workspace: skills, rules, profile, memory, tools and docs. Media and secrets stay on each machine. The workflow's name, owner and email come from `_workflow/me.json` (`{"name", "workflow", "email"}`); scripts read it, so the docs say "your workflow".

## Machines and paths
- The repo can sit anywhere: a folder on Windows, a folder in `~` on a Mac. Its root is env `GW_HOME`, else the folder the repo is in.
- **Code takes paths from `Common/tools/gwpaths.py` / `gwpaths.mjs`** (`ROOT`, `HOME_CLAUDE`, tool paths), so no drive letter or user folder is written in code. When you touch a script with a hard-coded root, switch it to gwpaths (the pre-commit guard warns about them).
- Read any absolute path in a doc as `<repo root>/...` on the machine you are on.

## Where things live
- **`_claude/`:** the one copy of your own Claude setup. `~/.claude` links here.
  - `skills/<name>/`: your skills (this one, `handoff`, `chat-review`, `working-style`, ...).
  - `agents/<name>.md`: `check-tiffin` (proves a handoff lost nothing), `check-progress` (is this loop converging?), `premium-critic` (strict polish review of anything you build).
  - `home/CLAUDE.md` + `home/working-style.md`: the global rules and your profile.
  - `handoffs/`: Tiffin box notes; `handoffs/said/`: said files (your verbatim words, plus `<said>.claude.md` with Claude's replies).
  - `chats/`: fair copies of every chat, per machine, with the index `CHATS-<machine>.md`.
- **`_workflow/`:** the engine.
  - `gw.py`: sync, notes, health, restore.
  - `LEDGER.md`: the workspace-wide ledger (projects keep their own `docs/LEDGER.md`).
  - `tiffin/`: `LEDGER-TEMPLATE.md`, `user_said.py` (writes said files), `ledger_check.py` (lists said-but-unledgered decisions).
  - `hooks/`: `context_meter` (says when the chat is heavy: 150k soft, 350k strong), `eta_reminder` (say what is starting and how long it takes before long jobs or helper agents), `ledger_nudge` (ledger a decision the turn it happens), `said_dump` (refreshes the said file before compaction and at session end; install with `install_said_dump.py`), `pre-commit` + `precommit_guard` (the guard).
- **`Common/tools/`:** tools any project can use.
  - `lan/`: open local pages on your phone. `serve.py <folder> <port>` serves a static page on the Wi-Fi; `phonecheck.py <port> [path]` tests the Wi-Fi address and prints the PC and phone links; `add_copybar.py` + `copybar.js` add a sticky copy bar to picker pages; `ALLOW_PHONE_ONCE.ps1` opens the ports to the home Wi-Fi once (Windows).
  - `chat-review/`: `chat_to_timeline.py` (transcript → clean timeline), `export_chats.py` (writes the fair copies), `token_usage.py` (tokens per chat).
  - `gwpaths.py` / `gwpaths.mjs`: paths for code.
- **`install/`:** `install_windows.ps1`, `install_mac.sh`.

## The ledger (written as you go)
The moment the user approves, rejects, corrects, gives a number or a preference, append one line to the project's `docs/LEDGER.md` (template `_workflow/tiffin/LEDGER-TEMPLATE.md`) with the user's words in quotes. When you pick between options yourself, append a CLAUDE-RULE line the same turn with BECAUSE and the options you dropped. The ledger, not the chat history, is what keeps detail across chats.

## Moving to a new chat
- Heavy chat at a step boundary, or the user says so → **Tiffin box**: skill `handoff`.
- **Continue a chat from the other machine** ("continue <chat title>"): find it in `_claude/chats/CHATS-<machine>.md`; read the project ledger in full and the chat's said file (`_claude/handoffs/said/<date>_<sid>.md`) first; then the fair copy from the END only for what those lack (fair copies keep the user's words in full but cut Claude's text to 700 characters, so they never settle a decision). Done when you can name the last user request, every PENDING ledger line and the step in progress, and the project folder is open.
- Media stays out of git: when the work needs a file missing on this machine, tell the user.

## Sync (automatic, the same on every machine)
- **One copy:** `~/.claude/skills/<own skill>`, `~/.claude/CLAUDE.md` and `~/.claude/working-style.md` are links into `_claude/`; edit either path, it is the same file.
- **Hooks:** SessionStart → `gw.py start` (commit local work, pull, heal links, report); Stop → `gw.py checkpoint` (push if changed and 15 min since the last push); SessionEnd → `gw.py end` (push). Pushing is automatic; carry on without asking. "Push now" = `python _workflow/gw.py push`.
- **Log the why:** `python _workflow/gw.py note "<what and why>"`. The notes become the commit message.
- **Every pull commits first**, then runs a plain `pull --rebase` (never `--autostash`, which can leave work stranded in a stash). If the start line warns about git stashes, compare each (`git stash show --stat stash@{N}`) with HEAD and ask the user before dropping one.
- **Guard:** the pre-commit hook blocks secrets, files over 20 MB, media/model files and nested repos. Fix the cause (add it to `.gitignore`) so the guard passes on its own.
- **Conflict** (two machines changed the same lines): the sync keeps both, undoes the rebase and names the file. Show both versions (`git diff HEAD @{u} -- <file>`), merge with the user's choice, commit, `gw.py push`. Push normally; keep history intact (no force-push).
- **Health:** `gw.py doctor`, `gw.py status`. History of a file: `gw.py restore <file> [rev]`. Remove the links: `gw.py undo-migration`.

## Set up a machine (once)
- **Windows:** `powershell -ExecutionPolicy Bypass -File install/install_windows.ps1`
- **Mac:** `bash install/install_mac.sh`

Both link skills, profile and memory, merge the shared settings and hooks, switch on the guard, and run `gw.py doctor`. Done when `gw.py doctor` passes on that machine.

## Before any script runs on the other machine
Setup scripts that pass on one machine often break on the other (a locked file, an existing folder, a library with no wheel there). Before you hand over a setup, sync or migration step:
- **Look at the real target first:** list the folders it will create or touch on THAT machine (ask the user to paste `ls` output if you can't see it). Treat every path as possibly there until the listing shows it empty.
- **Windows files can be locked** (running `.exe`, open editor): move aside or skip and retry, so a delete finishes whole or not at all.
- **Pin across machines only what must match**, and only to a version with a wheel for both.
- **Check what really matters** (e.g. `git ls-remote` for GitHub access).
- **Report by machine:** "tested on Windows; not run on the Mac yet". Say "works" only for a machine you ran it on.

Done when the target machine's real folders are listed and your report names the machine it was run on.
