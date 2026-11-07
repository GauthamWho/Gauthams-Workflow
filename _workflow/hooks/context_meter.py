"""Context meter hook (nickname "Auto meter": it ticks up as the chat goes on, like a taxi meter).
UserPromptSubmit: reads how big this chat's context is (from the last reply's token counts in the transcript) and,
when it crosses a level, asks Claude to tell the user in one plain line that the chat is heavy and how to hand off.

Why: every reply re-reads the WHOLE chat, so a 400k chat costs ~400k per reply, and very long contexts also lose
quality ("context rot"). Born from the 2026-11-06 token comparison: 2 chats used 90% of Windows tokens, 1 chat 86% on Mac.

Levels: 150k (soft; Matt Pocock's 'smart zone'), 350k (strong), then every +150k. Each level is said once per chat. Never blocks; errors = silent.
"""
import json, os, re, sys, tempfile

LEVELS = [150_000, 350_000, 500_000, 650_000, 800_000, 950_000]


def context_size(path):
    size = 0
    with open(path, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 3_000_000))  # the last replies are near the end
        tail = f.read().decode("utf-8", errors="replace").splitlines()
    for raw in reversed(tail):
        if '"usage"' not in raw or '"assistant"' not in raw:
            continue
        try:
            e = json.loads(raw)
        except Exception:
            continue
        if e.get("isSidechain"):
            continue
        u = (e.get("message") or {}).get("usage") or {}
        size = (u.get("input_tokens", 0) or 0) + (u.get("cache_read_input_tokens", 0) or 0) + \
            (u.get("cache_creation_input_tokens", 0) or 0)
        if size:
            break
    return size


def main():
    data = json.load(sys.stdin)
    path = data.get("transcript_path")
    if not path or not os.path.exists(path):
        return
    size = context_size(path)
    level = max([l for l in LEVELS if size >= l], default=0)
    if not level:
        return
    sid = re.sub(r"\W", "", str(data.get("session_id", "x")))[:40]
    stamp = os.path.join(tempfile.gettempdir(), f"claude-ctxmeter-{sid}")
    said = int(open(stamp).read() or 0) if os.path.exists(stamp) else 0
    if level <= said:
        return
    open(stamp, "w").write(str(level))
    k = size // 1000
    try:
        import pathlib
        sys.path.append(str(next(p for p in pathlib.Path(__file__).resolve().parents if (p / "Common/tools/gwpaths.py").exists()) / "Common/tools"))
        import gwpaths
        name = gwpaths.me()["name"]
        who = name.split()[0] if name else ""
    except Exception:
        who = ""
    pack = f"Pack the Tiffin {who}".strip()
    strong = level >= 350_000
    msg = (f"Context meter (user's rule, enforced by hook): this chat is now ~{k}k tokens, and every reply re-reads all of it. "
           + ("It is HEAVY: quality and the usage limit both suffer. " if strong else "")
           + "Do the user's request first. Then, at the end of your reply, add ONE plain line, e.g. "
           f"\"Auto meter: this chat is ~{k}k. "
           + ("Best to hand off now: " if strong else "When this task is done, ")
           + pack + ": say 'Tiffin box' and I'll pack a short note, then open a new chat in the same folder and paste the line I give you.\" "
           "If you are in the middle of a step that a new chat would have to redo, finish that step first and say so. "
           "Don't repeat this line later in the chat unless the meter fires again.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
