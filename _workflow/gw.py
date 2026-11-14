"""gw: your workflow engine. One repo = this folder, the same on every machine (PC and Mac).

Exactly ONE physical copy of everything lives in the repo; Claude's own folders only point at it:
  ~/.claude/skills/<own skill>   -> <repo>/_claude/skills/<name>      (junction on Windows, symlink on Mac)
  ~/.claude/CLAUDE.md            -> <repo>/_claude/home/CLAUDE.md     (file symlink)
  ~/.claude/working-style.md     -> <repo>/_claude/home/working-style.md
  ~/.claude/agents               -> <repo>/_claude/agents              (whole folder; agent definitions)
  ~/.claude/projects/<p>/memory  -> <repo>/_claude/memory/<windows name of p>
Installer skills (links into ~/.agents) and git-clone skills are left alone (listed in agents-skill-lock.json /
_workflow/nested-repos.json and reinstalled by setup).

Commands (python gw.py <cmd>):
  start              session start: commit local work, pull, heal links, report   (SessionStart hook)
  checkpoint         end of a turn: commit+push if changed and >=15 min      (Stop hook)
  end | push [msg]   commit + pull --rebase + push now                       (SessionEnd hook / "push now")
  note "<text>"      log why something changed (becomes the commit message)
  status             what is not on GitHub yet
  doctor             full health check, every item with a fix hint
  link               create/heal every link (also adopts new real skill folders)
  migrate            first-time move from the old mirror layout to links (does `link` + settings + guards)
  settings           merge _claude/settings.shared.json into ~/.claude/settings.json
  restore <path> [<rev>]   bring a file back from history (default: previous commit)
  undo-migration     put real folders/files back into ~/.claude (links removed)
  install-agent-skills   reinstall the installer-managed skills from _claude/agents-skill-lock.json (setup)
  clone-nested       clone/update the tool + skill repos listed in nested-repos.json (setup)
Never force-pushes. Never stashes: local work is committed before every pull (see safe_pull).
Never deletes anything outside the repo except links it created.
"""
import datetime, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIN = os.name == "nt"
HOME = Path.home()
CL = HOME / ".claude"
OUT = ROOT / "_claude"
WF = ROOT / "_workflow"
NOTES = WF / "PENDING-NOTES.md"          # machine-local (ignored)
STATE = WF / ".gw-state.json"             # machine-local (ignored)
PY = sys.executable
def _me():
    """the owner, from _workflow/me.json (written by the installer); falls back to git's own config."""
    try:
        return json.loads((Path(__file__).resolve().parent / "me.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


ME = _me()
NAME = ME.get("workflow") or "My Workflow"
WHO = (["-c", f"user.name={ME['name']}"] if ME.get("name") else []) + (["-c", f"user.email={ME['email']}"] if ME.get("email") else [])
MACHINE = "Windows" if WIN else "Mac"
HOME_FILES = ("CLAUDE.md", "working-style.md")


# ---------------------------------------------------------------- helpers
def git(*a, check=False, inp=None):
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", input=inp)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(a)}: {r.stderr.strip()[:300]}")
    return r


def is_link(p: Path) -> bool:
    try:
        return p.is_symlink() or (WIN and os.path.isjunction(p))
    except OSError:
        return False


def points_into(p: Path, target: Path) -> bool:
    try:
        return is_link(p) and Path(os.path.realpath(p)) == Path(os.path.realpath(target))
    except OSError:
        return False


def remove_link(p: Path):
    """remove a link only (never the target's contents)."""
    if p.is_symlink() and not p.is_dir():
        p.unlink()
    elif is_link(p):
        os.rmdir(p) if WIN else p.unlink()


def make_dir_link(link: Path, target: Path):
    link.parent.mkdir(parents=True, exist_ok=True)
    if WIN:
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, check=True)
    else:
        link.symlink_to(target, target_is_directory=True)


def make_file_link(link: Path, target: Path):
    link.parent.mkdir(parents=True, exist_ok=True)
    if WIN:
        subprocess.run(["cmd", "/c", "mklink", str(link), str(target)], capture_output=True, check=True)
    else:
        link.symlink_to(target)


def state(**upd):
    s = json.loads(STATE.read_text()) if STATE.exists() else {}
    if upd:
        s.update(upd)
        STATE.write_text(json.dumps(s, indent=1))
    return s


def mac_project(name: str) -> str:
    """memory folder name on this machine (the same name on every machine for the public workflow)."""
    return name


def win_project(local_name: str) -> str:
    return local_name


# ---------------------------------------------------------------- links
def link(report=True):
    msgs = []
    (OUT / "skills").mkdir(parents=True, exist_ok=True)
    (CL / "skills").mkdir(parents=True, exist_ok=True)
    # 1) adopt real skill folders in ~/.claude/skills (not clones, not installer links).
    #    All-or-nothing: copy into the repo, then MOVE the old folder aside in one rename (fails cleanly if a file is
    #    in use, e.g. a running .exe), then link. A skipped folder is retried at the next session start.
    trash = CL / ".gw-trash"
    for p in sorted((CL / "skills").iterdir()):
        if not p.is_dir() or is_link(p) or (p / ".git").exists():
            continue
        dst = OUT / "skills" / p.name
        try:
            for f in p.rglob("*"):
                if f.is_file():
                    d = dst / f.relative_to(p)
                    if not d.exists() or f.stat().st_mtime > d.stat().st_mtime + 1:
                        d.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, d)
            trash.mkdir(exist_ok=True)
            aside = trash / f"{p.name}-{int(time.time())}"
            os.rename(p, aside)                      # atomic: nothing is deleted if this fails
        except OSError as e:
            msgs.append(f"skipped skill {p.name} (in use: {getattr(e, 'filename', '') or e}; retried next session)")
            continue
        make_dir_link(p, dst)
        shutil.rmtree(aside, ignore_errors=True)     # leftovers (locked files) are cleaned next time
        msgs.append(f"adopted skill {p.name}")
    if trash.exists():
        for old in trash.iterdir():
            shutil.rmtree(old, ignore_errors=True)
    # 2) every repo skill is linked from ~/.claude/skills
    for sk in sorted((OUT / "skills").iterdir()):
        l = CL / "skills" / sk.name
        if points_into(l, sk):
            continue
        if is_link(l):
            remove_link(l)
        if not l.exists():
            make_dir_link(l, sk)
            msgs.append(f"linked skill {sk.name}")
    # 3) profile files (heal: an editor may have replaced a link with a real file)
    (OUT / "home").mkdir(parents=True, exist_ok=True)
    for f in HOME_FILES:
        l, t = CL / f, OUT / "home" / f
        if points_into(l, t):
            continue
        try:
            if l.exists() and not is_link(l):
                if not t.exists() or l.stat().st_mtime > t.stat().st_mtime + 1:
                    shutil.copy2(l, t)
                    msgs.append(f"took newer {f} into the repo")
                l.unlink()
            elif is_link(l):
                remove_link(l)
            if t.exists():
                make_file_link(l, t)
                msgs.append(f"linked {f}")
        except (OSError, subprocess.CalledProcessError) as e:
            if not l.exists() and t.exists():
                shutil.copy2(t, l)               # never leave the profile missing
            msgs.append(f"skipped {f} ({e})")
    # 3b) agent definitions: ~/.claude/agents -> <repo>/_claude/agents (whole folder; real files are adopted first)
    ag, agl = OUT / "agents", CL / "agents"
    ag.mkdir(parents=True, exist_ok=True)
    if not points_into(agl, ag):
        try:
            if agl.exists() and not is_link(agl):
                for f in agl.glob("*"):
                    if f.is_file() and (not (ag / f.name).exists() or f.stat().st_mtime > (ag / f.name).stat().st_mtime + 1):
                        shutil.copy2(f, ag / f.name)
                trash.mkdir(exist_ok=True)
                os.rename(agl, trash / f"agents-{int(time.time())}")
            elif is_link(agl):
                remove_link(agl)
            make_dir_link(agl, ag)
            msgs.append("linked agents")
        except OSError as e:
            msgs.append(f"skipped agents ({e})")
    # 4) memory folders
    for wm in sorted((OUT / "memory").glob("*")) if (OUT / "memory").exists() else []:
        l = CL / "projects" / mac_project(wm.name) / "memory"
        if points_into(l, wm):
            continue
        try:
            if l.exists() and not is_link(l):
                for f in l.glob("*"):
                    if f.is_file() and (not (wm / f.name).exists() or f.stat().st_mtime > (wm / f.name).stat().st_mtime + 1):
                        shutil.copy2(f, wm / f.name)
                trash.mkdir(exist_ok=True)
                os.rename(l, trash / f"memory-{wm.name}-{int(time.time())}")
            elif is_link(l):
                remove_link(l)
            make_dir_link(l, wm)
            msgs.append(f"linked memory {wm.name}")
        except OSError as e:
            msgs.append(f"skipped memory {wm.name} ({e})")
    # 6) installer skill list (for setup on other machines)
    lock = HOME / ".agents" / ".skill-lock.json"
    if lock.exists():
        dst = OUT / "agents-skill-lock.json"
        if not dst.exists() or lock.read_bytes() != dst.read_bytes():
            shutil.copy2(lock, dst)
    write_nested()
    if report and msgs:
        print("gw: " + "; ".join(msgs[:8]) + (f" (+{len(msgs) - 8} more)" if len(msgs) > 8 else ""))
    return msgs


def write_nested():
    found = []
    skip = {".git", "node_modules", "__pycache__", ".venv", ".venv-gw", "_claude"}
    for base, label in ((ROOT, "workspace"), (CL / "skills", "skills")):
        for dirpath, dirnames, _ in os.walk(base):
            dp = Path(dirpath)
            if dp != ROOT and (dp / ".git").exists():
                url = subprocess.run(["git", "-C", str(dp), "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
                found.append({"where": label, "path": dp.relative_to(base).as_posix(), "url": url or None})
                dirnames[:] = []
                continue
            dirnames[:] = [x for x in dirnames if x not in skip and not is_link(dp / x)]
    # merge, never drop: a fresh machine has not cloned them yet, so absence on disk means nothing
    p = WF / "nested-repos.json"
    old = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    seen = {(r["where"], r["path"]) for r in found}
    found += [r for r in old if (r["where"], r["path"]) not in seen]
    found.sort(key=lambda r: (r["where"], r["path"]))
    new = json.dumps(found, indent=1)
    if not p.exists() or p.read_text(encoding="utf-8") != new:
        p.write_text(new, encoding="utf-8")


# ---------------------------------------------------------------- settings
def settings():
    shared = json.loads((OUT / "settings.shared.json").read_text(encoding="utf-8"))
    sub = {"{{GW}}": ROOT.as_posix(), "{{HOME}}": HOME.as_posix(), "{{PY}}": "python" if WIN else "python3"}
    txt = json.dumps(shared)
    for k, v in sub.items():
        txt = txt.replace(k, v)
    shared = json.loads(txt)
    p = CL / "settings.json"
    cur = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    markers = shared.pop("_replace_hooks_containing", [])
    for event, groups in shared.pop("hooks", {}).items():
        mine = cur.setdefault("hooks", {}).setdefault(event, [])
        mine[:] = [g for g in mine if not any(any(m in h.get("command", "") for m in markers) for h in g.get("hooks", []))]
        mine.extend(groups)
    for k, v in shared.items():
        if isinstance(v, dict):
            cur.setdefault(k, {}).update(v)
        else:
            cur.setdefault(k, v)
    p.write_text(json.dumps(cur, indent=2), encoding="utf-8")
    print("gw: settings merged into", p)


def guards():
    git("config", "core.hooksPath", "_workflow/hooks")
    if not WIN:
        os.chmod(WF / "hooks" / "pre-commit", 0o755)


# ---------------------------------------------------------------- sync
def notes():
    return [l for l in NOTES.read_text(encoding="utf-8").splitlines() if l.startswith("- ")] if NOTES.exists() else []


def note(text):
    with NOTES.open("a", encoding="utf-8") as f:
        f.write(f"- {datetime.datetime.now():%Y-%m-%d %H:%M} [{MACHINE}] {text}\n")
    print("noted")


def changed():
    return [l[3:] for l in git("status", "--porcelain").stdout.splitlines()]


def ahead():
    r = git("rev-list", "--count", "@{u}..HEAD")
    return int(r.stdout.strip() or 0) if r.returncode == 0 else 0


def export_chats():
    """Fair copy of every chat on this machine into _claude/chats (so the other machine can read them)."""
    tool = ROOT / "Common" / "tools" / "chat-review" / "export_chats.py"
    if tool.exists():
        try:
            subprocess.run([sys.executable, str(tool)], cwd=ROOT, capture_output=True, timeout=180)
        except Exception:
            pass  # never block a sync on the chat export


def commit_local(msg="", label="Sync"):
    """Commit every local change (all chats' live edits). Returns (number of files, error or "")."""
    files = changed()
    if not files:
        return 0, ""
    n = notes()
    git("add", "-A")
    body = msg or ("\n".join(n) if n else "\n".join("- " + f for f in files[:30]))
    text = (f"{label} {datetime.date.today()} from {MACHINE}: {len(files)} file(s)\n\n{body}\n\n"
            "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    r = subprocess.run(["git", *WHO, "commit", "-q", "-F", "-"], cwd=ROOT, input=text, encoding="utf-8", capture_output=True, text=True)
    return len(files), ((r.stdout + r.stderr).strip()[:1500] if r.returncode else "")


def stashes():
    return git("stash", "list").stdout.splitlines()


def safe_pull():
    """Pull without ever parking work in a stash (2026-11-06: an --autostash pull hit a conflict, git kept the stash,
    exited 0, and 34 files of live edits vanished from disk). Local work is committed first, then a plain
    `pull --rebase` runs. A conflict aborts the rebase, so every local commit and file stays as it was.
    Returns (ok, message)."""
    before = len(stashes())
    gitdir = Path(git("rev-parse", "--absolute-git-dir").stdout.strip())
    rebasing = lambda: (gitdir / "rebase-merge").exists() or (gitdir / "rebase-apply").exists()
    for _ in range(3):  # another chat may write a file between our commit and the pull: commit again, retry
        n, err = commit_local()
        if err:
            return False, "commit BLOCKED by the guard, pull skipped (local files untouched):\n" + err
        r = git(*WHO, "pull", "--rebase", "-q")  # no --autostash: a dirty tree makes git refuse, it never stashes
        if r.returncode == 0 or rebasing():
            break
    if len(stashes()) > before:  # never expected; say it loudly rather than lose work
        return False, ("a STASH was created during the pull: run `git stash show --stat stash@{0}`, then "
                       "`git stash pop` to put the files back")
    if r.returncode == 0:
        return True, "pulled"
    if not rebasing():  # offline, or files kept changing: nothing was touched
        return False, "pull skipped, nothing changed here; will retry next sync (" + r.stderr.strip()[:160] + ")"
    both = sorted(git("diff", "--name-only", "--diff-filter=U").stdout.splitlines())  # the real conflicts
    git("rebase", "--abort")
    if not both:
        return False, "pull failed (rebase undone, nothing lost): " + (r.stderr or r.stdout).strip()[:200]
    state(conflict="The same lines were changed on both machines in: " + ", ".join(both[:10]))
    return False, ("CONFLICT with the other machine in: " + ", ".join(both[:10]) +
                   ". Your version is kept here (committed, on disk), the other machine's version is on GitHub; "
                   "nothing was overwritten or stashed. Ask Claude: 'resolve the sync conflict'.")


def push(msg="", quiet=False):
    link(report=not quiet)
    export_chats()
    files = changed()
    n = notes()
    nf, err = commit_local(msg)
    if err:
        print("gw: commit BLOCKED by the guard:\n" + err)
        return False
    if not files and not ahead():
        if not quiet:
            print("gw: nothing to push, up to date.")
        state(last_push=time.time())
        return True
    ok, m = safe_pull()
    if not ok:
        print("gw: " + m)
        return False
    r = git("push", "-q", "-u", "origin", "HEAD")
    if r.returncode:
        print("gw: push failed (kept locally, will retry next time): " + r.stderr.strip()[:300])
        return False
    if NOTES.exists():
        log = WF / "SYNC-LOG.md"
        with log.open("a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.datetime.now():%Y-%m-%d %H:%M} {MACHINE} pushed {git('rev-parse', '--short', 'HEAD').stdout.strip()}\n" + "\n".join(n) + "\n")
        NOTES.unlink()
        git("add", "_workflow/SYNC-LOG.md")
        subprocess.run(["git", *WHO, "commit", "-q", "-m", "sync log"], cwd=ROOT, capture_output=True)
        git("push", "-q")
    state(last_push=time.time(), conflict=None)
    if not quiet or files:
        print(f"gw: pushed {git('rev-parse', '--short', 'HEAD').stdout.strip()} ({len(files)} file(s)) from {MACHINE}.")
    publish_public(files)
    return True


def publish_public(files):
    """Optional public copy: rebuilt and pushed only when its leak scan passes (Windows only until tested on the Mac)."""
    pub = ROOT / "Export" / "tools" / "publish_public.py"
    if not (WIN and files and pub.exists()):
        return
    try:
        r = subprocess.run([sys.executable, str(pub), "--quiet"], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        out = (r.stdout + r.stderr).strip()
        if out:
            print("gw: " + out[-800:])
    except Exception as e:
        print(f"gw: public copy not updated ({e.__class__.__name__})")


def checkpoint():
    s = state()
    if time.time() - s.get("last_push", 0) < 15 * 60:
        return
    if changed() or ahead():
        push(quiet=True)
    else:
        state(last_push=time.time())


def start():
    s = state()
    if s.get("conflict"):
        print("gw: UNRESOLVED CONFLICT: " + s["conflict"] + ". Both versions are safe. Claude: show the user both "
              "versions (git diff HEAD @{u} -- <file>), merge with their choice, commit, then run gw.py push.")
    ok, pulled = safe_pull()  # commits local work first, never stashes
    if not ok:
        pulled = "PULL NOT DONE: " + pulled
    msgs = link(report=False)
    try:  # new shared hooks/settings from the other machine switch on by themselves
        import hashlib
        h = hashlib.sha1((OUT / "settings.shared.json").read_bytes()).hexdigest()
        if state().get("settings_hash") != h:
            settings()
            state(settings_hash=h)
            msgs.append("shared settings applied")
    except Exception as e:
        msgs.append(f"settings not applied ({e.__class__.__name__})")
    files, a = changed(), ahead()
    head = git("rev-parse", "--short", "HEAD").stdout.strip()
    line = f"{NAME} {head} ({MACHINE}): {pulled}"
    if msgs:
        line += "; " + "; ".join(msgs[:4])
    if files or a:
        line += f"; {len(files)} local change(s), {a} commit(s) not pushed (auto-push at the end of the session)"
    st = stashes()
    if st:
        line += (f"; WARNING {len(st)} git stash(es) may hold work that is NOT on disk ({st[0]}): "
                 "check with `git stash show --stat stash@{0}` before anything else")
    flag = WF / ".public-blocked.json"
    if flag.exists():
        line += ("; PUBLIC COPY BLOCKED (leak scan failed, nothing went public): tell the user and show "
                 + flag.name + "; fix the leak, then run Export/tools/publish_public.py")
    print(line)


def status():
    link(report=False)
    files, a = changed(), ahead()
    if not files and not a:
        print(f"{NAME}: up to date with GitHub.")
        return
    print(f"{NAME}: {len(files)} changed file(s), {a} commit(s) not pushed.")
    for f in files[:15]:
        print("  " + f)
    for l in notes()[-10:]:
        print(l)


# ---------------------------------------------------------------- doctor
def doctor():
    ok = True

    def chk(cond, name, fix=""):
        nonlocal ok
        print(("  OK   " if cond else "  FAIL ") + name + ("" if cond else f"   -> {fix}"))
        ok &= bool(cond)
    print(f"gw doctor ({MACHINE}, repo {ROOT})")
    git("fetch", "-q")
    chk(git("rev-parse", "HEAD").stdout == git("rev-parse", "@{u}").stdout, "same commit as GitHub", "python gw.py push / start")
    sk = list((OUT / "skills").iterdir())
    bad = [s.name for s in sk if not points_into(CL / "skills" / s.name, s)]
    chk(not bad, f"{len(sk)} own skills linked from ~/.claude/skills", f"python gw.py link  (missing: {bad[:5]})")
    for f in HOME_FILES:
        chk(points_into(CL / f, OUT / "home" / f), f"~/.claude/{f} links to the repo", "python gw.py link")
    mem = list((OUT / "memory").glob("*")) if (OUT / "memory").exists() else []
    badm = [m.name for m in mem if not points_into(CL / "projects" / mac_project(m.name) / "memory", m)]
    chk(not badm, f"{len(mem)} memory folders linked", "python gw.py link")
    st = (CL / "settings.json").read_text(encoding="utf-8") if (CL / "settings.json").exists() else ""
    chk(all(f"_workflow/gw.py{q} {c}" in st for c in ("start", "checkpoint", "end") for q in ('\\"',)),
        "session hooks installed (start/checkpoint/end)", "python gw.py settings")
    chk(git("config", "core.hooksPath").stdout.strip() == "_workflow/hooks", "pre-commit guard active", "python gw.py migrate")
    chk(git("ls-remote", "--heads", "origin").returncode == 0, "GitHub access (git can reach your repo)",
        "sign in once: git push (Git Credential Manager) or gh auth login")
    sys.path.insert(0, str(ROOT / "Common" / "tools"))
    try:
        import gwpaths
        chk(Path(gwpaths.ROOT) == ROOT, "gwpaths ROOT = this repo", "set GW_HOME")
    except Exception as e:
        chk(False, "gwpaths importable", str(e))
    lock = OUT / "agents-skill-lock.json"
    if lock.exists():
        names = json.loads(lock.read_text(encoding="utf-8"))["skills"].keys()
        miss = [n for n in names if not (CL / "skills" / n).exists() and not (HOME / ".agents" / "skills" / n).exists()]
        chk(not miss, f"{len(names)} installer skills present", f"setup reinstalls them ({len(miss)} missing)")
    nested = json.loads((WF / "nested-repos.json").read_text(encoding="utf-8"))
    missn = [r["path"] for r in nested if r["url"] and not ((ROOT if r["where"] == "workspace" else CL / "skills") / r["path"] / ".git").exists()]
    chk(not missn, f"{len(nested)} nested tool/skill repos present", f"setup clones them: {missn[:3]}")
    size = sum(int(l.split()[3]) for l in git("ls-tree", "-r", "-l", "HEAD").stdout.splitlines() if l.split()[3].isdigit())
    chk(size < 1e9, f"repo size {size / 1e6:.0f} MB (< 1 GB)", "move big folders into .gitignore")
    print("ALL OK" if ok else "Some checks failed: run the fix shown, or ask Claude to fix them.")
    return ok


# ---------------------------------------------------------------- recovery / misc
def restore(path, rev="HEAD~1"):
    r = git("checkout", rev, "--", path)
    print(f"gw: restored {path} from {rev}" if r.returncode == 0 else "gw: " + r.stderr.strip())


def undo_migration():
    for sk in (OUT / "skills").iterdir():
        l = CL / "skills" / sk.name
        if points_into(l, sk):
            remove_link(l)
            shutil.copytree(sk, l)
    for f in HOME_FILES:
        l = CL / f
        if is_link(l):
            remove_link(l)
            shutil.copy2(OUT / "home" / f, l)
    for wm in (OUT / "memory").glob("*"):
        l = CL / "projects" / mac_project(wm.name) / "memory"
        if is_link(l):
            remove_link(l)
            shutil.copytree(wm, l)
    print("gw: undone. ~/.claude has real folders/files again (the repo copies are untouched).")


def install_agent_skills():
    """re-create the installer-managed skills exactly as on the PC: clone each source repo once, copy each skill
    folder into ~/.agents/skills/<name>, link it from ~/.claude/skills/<name>, keep the lock file."""
    import tempfile
    lockp = OUT / "agents-skill-lock.json"
    if not lockp.exists():  # fresh install (e.g. the public copy): nothing installer-managed yet
        print("install-agent-skills: no agents-skill-lock.json yet, nothing to reinstall")
        return
    lock = json.loads(lockp.read_text(encoding="utf-8"))["skills"]
    agents = HOME / ".agents" / "skills"
    agents.mkdir(parents=True, exist_ok=True)
    by_src = {}
    for name, v in lock.items():
        by_src.setdefault(v["sourceUrl"], []).append((name, v["skillPath"]))
    done = 0
    with tempfile.TemporaryDirectory() as tmp:
        for i, (url, items) in enumerate(by_src.items()):
            todo = [(n, sp) for n, sp in items if not (agents / n).exists()]
            if todo:
                dst = Path(tmp) / f"s{i}"
                if subprocess.run(["git", "clone", "-q", "--depth", "1", url, str(dst)], capture_output=True).returncode:
                    print(f"gw: could not clone {url}")
                    continue
                for n, sp in todo:
                    src = (dst / sp).parent
                    if src.exists():
                        shutil.copytree(src, agents / n, ignore=shutil.ignore_patterns(".git"))
                        done += 1
            for n, _ in items:
                l = CL / "skills" / n
                if (agents / n).exists() and not l.exists() and not is_link(l):
                    make_dir_link(l, agents / n)
    shutil.copy2(lockp, HOME / ".agents" / ".skill-lock.json")
    print(f"gw: installer skills: {done} installed, {len(lock)} in the list")


def rewritten_repos():
    """Nested repos whose GitHub history was rewritten on purpose ({path: date, why}); _workflow/rewritten-repos.json.
    Use: list a repo here only when its history was rewritten on purpose, so another machine's copy cannot
    fast-forward any more (none listed today; added 2026-11-13)."""
    p = WF / "rewritten-repos.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def reclone_rewritten(dst, url):
    """Replace a stale copy of a rewritten repo with a fresh clone. Never loses work: if the copy has uncommitted
    changes or commits that never reached GitHub, it is only set aside (renamed) and the user is told."""
    run = lambda *a: subprocess.run(["git", "-C", str(dst), *a], capture_output=True, text=True)
    dirty = run("status", "--porcelain").stdout.strip()
    # compare with the copy's OWN last-known GitHub state (before any fetch): commits beyond it never reached GitHub
    has_u = run("rev-parse", "@{u}").returncode == 0
    unpushed = run("log", "--oneline", "@{u}..HEAD").stdout.strip() if has_u else run("log", "--oneline", "-1").stdout.strip()
    aside = dst.with_name(dst.name + ".before-rewrite")
    if aside.exists():
        print("gw: STOP:", aside, "already exists; remove it by hand, then run again")
        return
    dst.rename(aside)
    if subprocess.run(["git", "clone", "-q", url, str(dst)]).returncode != 0:
        aside.rename(dst)
        print("gw: re-clone failed; old copy put back:", dst)
        return
    if dirty or unpushed:
        print("gw: fresh copy of", dst.name, "made; your old copy had local work and was KEPT at", aside)
    else:
        def _force(fn, path, _exc):   # git marks object files read-only (Windows): make writable, then delete
            os.chmod(path, 0o700); fn(path)
        shutil.rmtree(aside, onerror=_force)
        print("gw: fresh copy of", dst.name, "made (its GitHub history was cleaned on purpose; the old copy had no local work)")


def clone_nested():
    for r in json.loads((WF / "nested-repos.json").read_text(encoding="utf-8")):
        if not r["url"]:
            print("gw: skip (no remote):", r["path"])
            continue
        dst = (ROOT if r["where"] == "workspace" else CL / "skills") / r["path"]
        if (dst / ".git").exists():
            git_r = subprocess.run(["git", "-C", str(dst), "pull", "-q", "--ff-only"], capture_output=True)
            if git_r.returncode != 0 and r["path"] in rewritten_repos():
                reclone_rewritten(dst, r["url"])
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        print("gw: clone", r["url"])
        subprocess.run(["git", "clone", "-q", r["url"], str(dst)])


def migrate():
    link()
    settings()
    guards()
    print("gw: migration done. Run: python gw.py doctor")


if __name__ == "__main__":
    a = sys.argv[1:] or ["status"]
    cmd, rest = a[0], a[1:]
    try:
        if cmd == "start":
            start()
        elif cmd == "checkpoint":
            checkpoint()
        elif cmd in ("end", "push"):
            push(" ".join(rest), quiet=(cmd == "end"))
        elif cmd == "note":
            note(" ".join(rest))
        elif cmd == "status":
            status()
        elif cmd == "doctor":
            sys.exit(0 if doctor() else 1)
        elif cmd == "link":
            link()
        elif cmd == "settings":
            settings()
        elif cmd == "migrate":
            migrate()
        elif cmd == "restore":
            restore(*rest)
        elif cmd == "undo-migration":
            undo_migration()
        elif cmd == "install-agent-skills":
            install_agent_skills()
        elif cmd == "clone-nested":
            clone_nested()
        else:
            print(__doc__)
    except Exception as e:   # hooks must never break a Claude session
        if cmd in ("start", "checkpoint", "end"):
            print(f"gw {cmd}: {e}")
        else:
            raise
