"""Adds the said_dump hook (PreCompact + SessionEnd) to ~/.claude/settings.json. Run once; safe to re-run."""
import json, os
from pathlib import Path
p = os.path.expanduser("~/.claude/settings.json")
d = json.load(open(p, encoding="utf-8"))
hooks = d.setdefault("hooks", {})
cmd = f'python "{(Path(__file__).resolve().parent / "said_dump.py").as_posix()}"'
entry = {"hooks": [{"type": "command", "command": cmd, "timeout": 60}]}
for ev in ("PreCompact", "SessionEnd"):
    lst = hooks.setdefault(ev, [])
    if not any(cmd in json.dumps(h) for h in lst):
        lst.insert(0, entry)
        print(f"added to {ev}")
    else:
        print(f"already in {ev}")
json.dump(d, open(p, "w", encoding="utf-8"), indent=2)
print("settings.json saved")
