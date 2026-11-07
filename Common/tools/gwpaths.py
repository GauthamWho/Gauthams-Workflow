"""Machine-independent paths for the workflow tools (Windows and Mac).
    from gwpaths import ROOT, ROOT_FWD, NODE, NPX, HOME_CLAUDE, me
ROOT = env GW_HOME, else the folder this repo is in (any drive, any clone folder).  ROOT_FWD = ROOT with forward slashes.
me() = who this workflow belongs to: <ROOT>/_workflow/me.json {"name": "Alex", "workflow": "Alex's Workflow", "email": ""},
       else git's global user.name / user.email and the workflow name "My Workflow".
JS twin: gwpaths.mjs (same names).

Scripts elsewhere in the repo find this module with one line:
    import sys, pathlib; sys.path.append(str(next(p for p in pathlib.Path(__file__).resolve().parents if (p / "Common/tools/gwpaths.py").exists()) / "Common/tools")); import gwpaths
"""
import json, os, shutil, subprocess
from pathlib import Path

WIN = os.name == "nt"
# the repo is wherever this file sits (<ROOT>/Common/tools/gwpaths.py), so any clone folder works
ROOT = Path(os.environ.get("GW_HOME") or Path(__file__).resolve().parents[2])
ROOT_FWD = ROOT.as_posix()
HOME_CLAUDE = Path.home() / ".claude"
ME_FILE = ROOT / "_workflow" / "me.json"

NODE = shutil.which("node") or "node"
NPX = shutil.which("npx") or "npx"   # npx.cmd on Windows (found through PATHEXT)


def _git_global(key):
    try:
        r = subprocess.run(["git", "config", "--global", key], capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return ""


def me():
    """{"name", "workflow", "email"} from _workflow/me.json, else git global user.name/email + "My Workflow"."""
    d = {}
    try:
        d = json.loads(ME_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    name = d.get("name") or _git_global("user.name")
    return {
        "name": name,
        "workflow": d.get("workflow") or "My Workflow",
        "email": d.get("email") or _git_global("user.email"),
    }
