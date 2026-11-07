"""said_dump.py - PreCompact + SessionEnd hook: keep the user's words before anything can summarise them.

Claude Code's compaction replaces the early chat with a summary ("This session is being continued..."); after that the
user's exact early words exist only in the transcript file. This hook runs user_said.py on the current transcript so the
verbatim said file in _claude/handoffs/said/ is always current, and (PreCompact only) tells Claude to ledger any decision
from this chat that is not in docs/LEDGER.md yet, BEFORE the summary is written.

Why: 2026-11-07 handoff audit - early user turns of two chats survived only inside compaction summaries.
Never blocks; errors = silent.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
USER_SAID = os.path.join(HERE, "..", "tiffin", "user_said.py")


def main():
    data = json.load(sys.stdin)
    path = data.get("transcript_path")
    if not path or not os.path.exists(path):
        return
    out = ""
    try:
        r = subprocess.run([sys.executable, USER_SAID, path], capture_output=True, text=True, timeout=40)
        out = (r.stdout or "").strip().splitlines()
    except Exception:
        out = []
    said = out[0] if out else "(said file not written)"
    if data.get("hook_event_name") == "PreCompact":
        msg = ("Said file (user's rule, enforced by hook): this chat is about to be compacted into a summary. The user's verbatim "
               f"words are saved at {said}. Before the summary, append to the project's docs/LEDGER.md every approve / reject / "
               "correction / number / preference from this chat that is not there yet (user's words in quotes), and make sure the "
               "ledger's Chats list names this said file. The summary may then be short: the detail lives in those two files.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreCompact", "additionalContext": msg}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
