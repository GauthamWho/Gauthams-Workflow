"""ETA reminder hook (the "seat-belt beep"). PreToolUse: when a chat starts helper agents, a workflow, a background
job or a long render, put a one-line reminder in front of the chat: tell the user what is starting and roughly how
long it takes. Born from the 2026-11-06 chat review (Bigg Boss): the ETA rule was written down but skipped mid-work.

Never blocks anything; any error = silent exit 0. Throttled to once per 3 minutes per chat (a batch of 4 agents gives
one reminder, not four).
"""
import json, os, re, sys, tempfile, time

LONG_BASH = re.compile(r"remotion\s+render|npx\s+remotion\s+render|render\.mjs|ffmpeg\b.*-i\b|whisper|voice_check|earshot|"
                       r"pip\s+install|npm\s+(install|ci)\b|git\s+clone", re.I)
REMINDER = ("ETA rule (user's working-style, enforced by hook): in your next message to the user, say in ONE plain line "
            "what is starting and about how long it will take (e.g. \"Starting 4 builders: cards, chrome, ui, objects. About 6 min.\"). "
            "While it runs, send a 1-line status as parts finish (done / still running / next). If you can't estimate, say so and why.")


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    hit = tool in ("Agent", "Task", "Workflow")
    if tool in ("Bash", "PowerShell"):
        hit = bool(inp.get("run_in_background")) or bool(LONG_BASH.search(str(inp.get("command", ""))))
    if not hit:
        return
    sid = re.sub(r"\W", "", str(data.get("session_id", "x")))[:40]
    stamp = os.path.join(tempfile.gettempdir(), f"claude-eta-{sid}")
    if os.path.exists(stamp) and time.time() - os.path.getmtime(stamp) < 180:
        return
    open(stamp, "w").close()
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": REMINDER}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
