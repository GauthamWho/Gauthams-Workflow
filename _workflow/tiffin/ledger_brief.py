r"""ledger_brief.py - what a NEW chat reads from a project's LEDGER.md, by the project's memory mode.

Usage:
  python ledger_brief.py <LEDGER.md>                    follows the ledger's own "Memory mode:" line (default: full)
  python ledger_brief.py <LEDGER.md> --mode full|rules|lookup [--chats N]

Memory modes (the user picks one when the project starts; it is written in the ledger header as
`Memory mode: full` / `rules` / `lookup`; user 2026-11-08: "we will have only the student 1 / we can also have
student 4, and Student 3 / based on teh users need"):
  full    "Whole notebook" (DEFAULT). Prints the whole ledger. Safest: nothing to remember to look up.
  rules   "Short notes + your rules". Open items + the last N chats + every old PREF / REJECTED / CORRECTED /
          DECISION / APPROVED / PICK / VERDICT line, + a look-up line for the rest.
  lookup  "Short notes + look-up". Open items + the last N chats only, + a look-up line. Lightest; the chat must
          search the full ledger before deciding anything about an older topic.
Recall test 2026-11-08 (12 questions, fresh chats, twice each; _workflow/docs/check/RECALL-TEST-2026-11-08.md):
  full 12/12 | rules 10/12 without searching | lookup 3/12 without searching, 12/12 when it searched.

The ledger file is never changed or cut; check-tiffin PACK always reads all of it. "Open" = status PENDING / OPEN /
BLOCKED / "in progress", or "not verified" / "NOT checked"; a status starting DONE, or a ~~struck~~ line, is closed.
"""
import re, sys
from pathlib import Path

OPEN = re.compile(r"\|\s*(PENDING|OPEN|BLOCKED)\b|\bin progress\b|not verified|NOT checked|NOT verified", re.I)
TAG = re.compile(r"^- \[(\d{4}-\d{2}-\d{2})(?: (?:\d{2}:\d{2}|chat (\d+)))?[^\]]*\]")
RULE = re.compile(r"^- (?:~~)?\[[^\]]*\] (PREF|REJECTED|CORRECTED|DECISION|APPROVED|PICK|VERDICT)(?![A-Z])")
MODE = re.compile(r"(?im)^\W*Memory mode\W*:?\W*(full|rules|lookup)\b")
MODES = ("full", "rules", "lookup")


def ledger_mode(text: str) -> str:
    m = MODE.search(text[:4000])
    return m.group(1).lower() if m else "full"


def brief(path: Path, n_chats: int = 2, mode: str = "") -> str:
    text = path.read_text(encoding="utf-8")
    mode = mode or ledger_mode(text)
    if mode == "full":
        return f"<!-- memory mode: full (whole notebook) -->\n{text}" if not text.endswith("\n") else \
            f"<!-- memory mode: full (whole notebook) -->\n{text}"
    rules = mode == "rules"
    lines = text.splitlines()
    first = next((i for i, l in enumerate(lines) if TAG.match(l)), len(lines))
    head = lines[:first]
    while head and head[-1].startswith("## ") or (head and not head[-1].strip()):
        head = head[:-1]                                       # drop an empty trailing section heading
    chats_at = next((i for i, l in enumerate(head) if l.startswith("## Chats")), None)
    if chats_at is not None:                                   # shorten the Chats list, keep its newest 5 entries
        end = next((i for i in range(chats_at + 1, len(head)) if head[i].startswith("## ")), len(head))
        items = [l for l in head[chats_at + 1:end] if l.startswith("- ")]
        keep = items[-5:]
        older = len(items) - len(keep)
        head = head[:chats_at + 1] + ([f"- ({older} older chats: see the full ledger)"] if older else []) + keep + \
            [""] + head[end:]
    body = lines[first:]
    tags = [TAG.match(l) for l in body]
    chat_nums = sorted({int(m.group(2)) for m in tags if m and m.group(2)})
    dates = sorted({m.group(1) for m in tags if m})
    recent_chats = set(chat_nums[-n_chats:])
    recent_dates = set(dates[-n_chats:]) if not chat_nums else set()

    def recent(m):
        if not m:
            return False
        return (m.group(2) and int(m.group(2)) in recent_chats) or (m.group(1) in recent_dates)

    open_l, recent_l, rule_l, skipped, section = [], [], [], 0, ""
    for l, m in zip(body, tags):
        if l.startswith("## "):
            section = l
            continue
        if not l.startswith("- ["):                            # undated bullets count only in an "Open ..." section
            if l.startswith("- ") and re.search(r"(?i)open", section) and l.strip() != "- none":
                open_l.append(l)
            continue
        closed = l.lstrip("- ").startswith("~~") or ("|" in l and l.rsplit("|", 1)[1].strip().upper().startswith("DONE"))
        if recent(m):
            recent_l.append(l)
        elif OPEN.search(l) and not closed:
            open_l.append(l)
        elif rules and RULE.match(l):
            rule_l.append(l)
        else:
            skipped += 1
    which = f"chats {', '.join(map(str, sorted(recent_chats)))}" if recent_chats else f"dates {', '.join(sorted(recent_dates))}"
    label = "short notes + your rules" if rules else "short notes + look-up"
    out = [f"<!-- memory mode: {mode} ({label}) -->"] + head + \
        ["", f"## OPEN from older chats ({len(open_l)}): do these first"] + (open_l or ["- none"])
    if rules:
        out += ["", f"## Old rules, rejections and corrections ({len(rule_l)}): never undo these without asking"] + rule_l
    out += ["", f"## Last {which} in full ({len(recent_l)} lines)"] + recent_l
    out += ["", f"## Not shown: {skipped} older lines. Before deciding ANYTHING about an older topic, look it up:",
            f'`grep -n -i "<topic word>" "{path.as_posix()}"`']
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        raise SystemExit(__doc__)
    n = int(a[a.index("--chats") + 1]) if "--chats" in a else 2
    mode = a[a.index("--mode") + 1] if "--mode" in a else ""
    if mode and mode not in MODES:
        raise SystemExit(f"--mode must be one of {MODES}")
    sys.stdout.reconfigure(encoding="utf-8")
    print(brief(Path(a[0]), n, mode), end="")
