r"""ledger_brief.py - the short read of a LEDGER.md for a new chat (so a long ledger never makes the new chat heavy).

Usage:
  python ledger_brief.py <LEDGER.md> [--chats N]     (default: the last 2 chats in full)

Why: a new chat used to read the whole ledger. It grows with every chat (85 KB after 14 chats), so after ~50 chats
the new chat would start almost as heavy as the old one (user 2026-11-08: "make this update").
The ledger file itself is never changed or cut: it stays the one complete record, and check-tiffin PACK still reads
all of it. This script only prints what a new chat must act on:
  1. the header (everything before the first decision line),
  2. the last 5 entries of the Chats list (said-file paths) + how many older ones exist,
  3. every OPEN item: status PENDING / OPEN / BLOCKED / "in progress", or "not verified" / "NOT checked" anywhere,
  4. every line of the last N chats (by the "[date chat N]" tag; ledgers without chat tags: the last N dates),
  5. a footer: how many lines were left out and the grep line to search them by topic.
Struck-through lines (~~...~~) count as closed.
"""
import re, sys
from pathlib import Path

OPEN = re.compile(r"\|\s*(PENDING|OPEN|BLOCKED)\b|\bin progress\b|not verified|NOT checked|NOT verified", re.I)
TAG = re.compile(r"^- \[(\d{4}-\d{2}-\d{2})(?: (?:\d{2}:\d{2}|chat (\d+)))?[^\]]*\]")


def brief(path: Path, n_chats: int = 2) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    first = next((i for i, l in enumerate(lines) if TAG.match(l)), len(lines))
    head = lines[:first]
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

    open_l, recent_l, skipped, section = [], [], 0, ""
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
        else:
            skipped += 1
    which = f"chats {', '.join(map(str, sorted(recent_chats)))}" if recent_chats else f"dates {', '.join(sorted(recent_dates))}"
    out = head + [f"## OPEN from older chats ({len(open_l)}): do these first"] + (open_l or ["- none"]) + \
        ["", f"## Last {which} in full ({len(recent_l)} lines)"] + recent_l + \
        ["", f"## Not shown: {skipped} closed lines from older chats. Search them by topic before deciding anything "
             f"about it:", f'`grep -n -i "<topic word>" "{path.as_posix()}"`']
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    n = int(a[a.index("--chats") + 1]) if "--chats" in a else 2
    sys.stdout.reconfigure(encoding="utf-8")
    print(brief(Path(a[0]), n), end="")
