"""Ledger nudge hook (UserPromptSubmit).

When the user's message looks like a DECISION (approve, reject, correct, a number, a preference, "always/never"),
tell Claude to append it to the project's docs/LEDGER.md in this same turn - so the ledger is written the moment
decisions happen, not reconstructed from memory at Tiffin-box time.

Why: 2026-11-07 - the user felt quality dropped after moving from one long chat to Tiffin-box handoffs.
A summary at the end can forget; a ledger written as you go cannot. Never blocks; errors = silent.
"""
import json, re, sys
from pathlib import Path

TEMPLATE = (Path(__file__).resolve().parents[1] / "tiffin" / "LEDGER-TEMPLATE.md").as_posix()

DECISION = re.compile(
    r"\b(approve|approved|ok|okay|go|yes|love|like this|perfect|keep|lock|final)\b"
    r"|\b(no|not|don'?t|never|always|instead|wrong|rejected?|hate|remove|change|fix|should|must)\b"
    r"|\b\d+(\.\d+)?\s*(fps|s|sec|seconds|min|px|%|k|frames?|words?|cards?|lines?)\b"
    r"|\b(prefer|from now on|rule|remember)\b",
    re.I,
)
SKIP = ("<local-command", "<command-name", "<system-reminder", "[Request interrupted")


def main():
    data = json.load(sys.stdin)
    prompt = (data.get("prompt") or "").strip()
    if not prompt or prompt.startswith(SKIP) or len(prompt) < 8:
        return
    if not DECISION.search(prompt):
        return
    msg = ("Ledger (user's rule, enforced by hook): this message contains a decision, correction, number or preference. "
           f"Before this turn ends, append it to the project's docs/LEDGER.md (format in {TEMPLATE}; "
           "create the file from the template if the project has none). Quote the user's words verbatim, then what you changed and where. "
           "A preference that stays true next month also goes to working-style.md or the format's skill. "
           "If this message is not really a decision, do nothing and say nothing about this note.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
