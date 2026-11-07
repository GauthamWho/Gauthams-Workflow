"""Make this workflow yours. Run by install_windows.ps1 / install_mac.sh (or directly: python install/setup_me.py).

1. Asks your name and your workflow's name (example: Alex -> "Alex's Workflow"), writes _workflow/me.json.
2. Fills your name into _claude/home/CLAUDE.md.
3. Backs up your current ~/.claude/CLAUDE.md, working-style.md and agents/ (nothing is lost).
4. Links Claude Code to this folder (python _workflow/gw.py migrate): skills, rules, agents, hooks.
5. Optional: makes your own private GitHub copy, so your PC and Mac stay in sync.
Safe to run again.
"""
import datetime, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ME = ROOT / "_workflow" / "me.json"
CL = Path.home() / ".claude"


def ask(q, default=""):
    a = input(f"{q}{f' [{default}]' if default else ''}: ").strip()
    return a or default


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)


def main():
    old = json.loads(ME.read_text(encoding="utf-8")) if ME.exists() else {}
    print("\nMake this workflow yours.\n")
    name = ask("Your first name (example: Alex)", old.get("name", ""))
    while not name:
        name = ask("Your first name (example: Alex)")
    workflow = ask("Your workflow's name", old.get("workflow") or f"{name}'s Workflow")
    email = ask("Email for your saves to git (optional)", old.get("email") or git("config", "--global", "user.email").stdout.strip())
    ME.write_text(json.dumps({"name": name, "workflow": workflow, "email": email}, indent=1) + "\n", encoding="utf-8")
    print(f"  saved {ME.relative_to(ROOT)}")

    home = ROOT / "_claude" / "home" / "CLAUDE.md"
    t = home.read_text(encoding="utf-8")
    if "{{NAME}}" in t or "{{WORKFLOW}}" in t:
        home.write_text(t.replace("{{NAME}}", name).replace("{{WORKFLOW}}", workflow), encoding="utf-8")
        print("  filled your name into _claude/home/CLAUDE.md")

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = CL / f"backup-before-workflow-{stamp}"
    for f in ("CLAUDE.md", "working-style.md", "agents", "settings.json"):
        p = CL / f
        if p.exists() and not p.is_symlink():
            backup.mkdir(parents=True, exist_ok=True)
            (shutil.copytree if p.is_dir() else shutil.copy2)(p, backup / f)
    if backup.exists():
        print(f"  backed up your old Claude files to {backup}")
        for f in ("CLAUDE.md", "working-style.md"):           # the workflow's versions win; yours stay in the backup
            p = CL / f
            if p.exists() and not p.is_symlink():
                p.unlink()

    r = subprocess.run([sys.executable, str(ROOT / "_workflow" / "gw.py"), "migrate"])
    if r.returncode:
        sys.exit("Linking failed. Ask Claude: 'run python _workflow/gw.py doctor and fix it'.")

    remotes = git("remote", "-v").stdout
    if "upstream" not in remotes and "origin" in remotes:
        git("remote", "rename", "origin", "upstream")         # the shared original stays reachable as 'upstream'
    if "origin" not in git("remote").stdout.split():
        if shutil.which("gh") and ask("Make your own PRIVATE GitHub copy now, for sync between your machines? (y/n)", "y").lower().startswith("y"):
            slug = "".join(c if c.isalnum() else "-" for c in workflow).strip("-")
            git("add", "-A")
            git("commit", "-q", "-m", f"{workflow}: first setup")
            subprocess.run(["gh", "repo", "create", slug, "--private", "--source", str(ROOT), "--remote", "origin", "--push"])
        else:
            print("  Sync stays on this machine for now. Later: create a private GitHub repo and run\n"
                  "    git remote add origin <its URL>   then   python _workflow/gw.py push")
    print(f"\nDone. Open Claude Code in {ROOT} and say: \"read my working style\".\n"
          "Health check any time: python _workflow/gw.py doctor\n")


if __name__ == "__main__":
    main()
