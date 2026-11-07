<!-- Pictures are code-drawn (built in the owner's private workspace) and counted from this repo. -->

<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/hero-notebook-dark.svg">
  <img src="docs/readme/hero-notebook-light.svg" alt="Gautham's Workflow: Gautham stands beside the title; counters show 5 home-made skills plus 24 adopted, 3 checker agents, and a quality line that climbs" width="100%">
</picture>
</p>

<p align="center"><b>Every decision you make is kept word for word, checked by reviewers, and carried into every future chat.<br>Quality only goes up.</b><br>A way of working with Claude Code for any work: apps, websites, writing, anything.<br>Install it and it becomes <b>your</b> workflow, with your name on it.</p>

<p align="center">
<a href="#1-why-plain-claude-drops-quality">The problem</a> ·
<a href="#2-the-answer-the-tiffin-box">The answer</a> ·
<a href="#4-two-examples">Examples</a> ·
<a href="#7-what-you-say-what-happens">What to say</a> ·
<a href="#10-install">Install</a>
</p>

---

## 1. Why plain Claude drops quality

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s01-leak-dark.svg">
  <img src="docs/readme/s01-leak-light.svg" alt="A chat grows, its early messages fade, and the handoff note loses details" width="100%">
</picture>

Long chats forget their beginning. Short notes between chats drop details. We measured it on our own old handoffs:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s01-audit-dark.svg">
  <img src="docs/readme/s01-audit-light.svg" alt="Of 52 decisions in two old handoffs: 67% kept in the note, 27% only in other files, 6% lost" width="100%">
</picture>

## 2. The answer: the Tiffin box

The **Tiffin box** is the handoff between chats, named after the Indian stacked lunch box. Each tier holds one thing, packed whole, never squashed into a summary.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s02-tiffin-dark.svg">
  <img src="docs/readme/s02-tiffin-light.svg" alt="A tiffin carrier stacks four tiers: your words, Claude's words, the LEDGER and a short note, then a check-tiffin PASS stamp" width="100%">
</picture>

Across many chats, nothing is re-summarised: the LEDGER and your words only grow, and every new chat reads them first.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s02-compare-dark.svg">
  <img src="docs/readme/s02-compare-light.svg" alt="Comparison: plain Claude, plus downloaded skills, and Gautham's Workflow across five abilities" width="100%">
</picture>

## 3. One task = one chat

A task is one dish, so it gets one cook. Hand over only when the cook is tired, and then hand over everything.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s03-cook-dark.svg">
  <img src="docs/readme/s03-cook-light.svg" alt="Five cooks with five cards make a different dish; one cook passing a whole tiffin box makes the same dish" width="100%">
</picture>

Big apps can still be cut into tickets. Work that needs one person's taste stays in one chat.

## 4. Two examples

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s10-todo-dark.svg">
  <img src="docs/readme/s10-todo-light.svg" alt="Build a to-do app: grill me first, write the plan, cut into tickets, build with tests, reviewers check it, Tiffin box hand-over; a phone fills into the finished app" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s10-bug-dark.svg">
  <img src="docs/readme/s10-bug-light.svg" alt="Fix a bug on a website: tell what broke, diagnose this, fix plus a test, reviewer passes it, lesson saved; a broken Pay button becomes a working one" width="100%">
</picture>

## 5. Checkers judge it before you see it

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s04-line-dark.svg">
  <img src="docs/readme/s04-line-light.svg" alt="The work moves along a belt past plan, build and test, then through three checker gates (nothing lost, really fixed?, picky tester) that each turn green" width="100%">
</picture>

Three checkers come with it: **check-tiffin** (a handoff lost nothing), **check-progress** (are the fixes really working?) and **premium-critic** (a very picky tester). Add your own in [`_claude/agents/`](_claude/agents/).

## 6. Why it gets better every week

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s05-loop-dark.svg">
  <img src="docs/readme/s05-loop-light.svg" alt="Loop: you correct, the LEDGER keeps your words, the checker rulebook learns, the next job passes, you correct less" width="100%">
</picture>

**Bigg Boss** (a nickname: it watches every chat) audits old chats for mistakes that came back. **Retro** runs after every build.

## 7. What you say, what happens

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s06-phrases-dark.svg">
  <img src="docs/readme/s06-phrases-light.svg" alt="Eight phrase cards: New project grill me first, Is it working, Premium check, Tiffin box, Continue chat, Bigg Boss, Diagnose this, Retro" width="100%">
</picture>

## 8. Skills: borrowed, then made our own

We start from the best public skills and reshape them around how we work. Three of [Matt Pocock's](https://github.com/mattpocock/skills), before and after:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s08-before-after-dark.svg">
  <img src="docs/readme/s08-before-after-light.svg" alt="Three of Matt Pocock's public skills and what we changed in each" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s10-yours-dark.svg">
  <img src="docs/readme/s10-yours-light.svg" alt="Make it your own: four people each draw a different circle" width="100%">
</picture>

Take what helps from anyone's skills (ours too), then shape it to your own taste.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s08-groups-dark.svg">
  <img src="docs/readme/s08-groups-light.svg" alt="29 skills grouped by job, 5 home-made and 24 adopted" width="100%">
</picture>

Every skill lives in [`_claude/skills/`](_claude/skills/), each with its own `SKILL.md`. Who made each adopted one: [THIRD-PARTY.md](THIRD-PARTY.md).

## 9. Survives anything

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/s09-sync-dark.svg">
  <img src="docs/readme/s09-sync-light.svg" alt="PC and Mac sync through your own private GitHub repo every 15 minutes; when the PC is lost, a new laptop gets everything back with one command" width="100%">
</picture>

## 10. Install

You need [Claude Code](https://claude.com/claude-code), git and Python 3.10+.

1. Clone it and step inside:
   ```bash
   git clone https://github.com/GauthamWho/Gauthams-Workflow.git
   cd Gauthams-Workflow
   ```
2. Run the installer. It asks your name, so the workflow becomes yours (for example "Alex's Workflow"), and offers to make your own private copy on GitHub.
   - Windows: right-click `install\install_windows.ps1` → **Run with PowerShell**
   - Mac / Linux:
     ```bash
     sh install/install_mac.sh
     ```
3. Open Claude Code in the folder and say: **"New project: \<your idea\>. Grill me first."**

Sync, the ledger and the checks then run on their own.

## Credits

Made by **Gautham**: [github.com/GauthamWho](https://github.com/GauthamWho) · [instagram.com/gauthamwho](https://instagram.com/gauthamwho).
Licence: Apache-2.0 ([LICENSE](LICENSE)). If you share or build on this, keep the [NOTICE](NOTICE) so the credit links stay. Third-party skills keep their own licences: [THIRD-PARTY.md](THIRD-PARTY.md).
