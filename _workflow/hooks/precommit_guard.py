"""Pre-commit guard for the workflow repo. Exit 1 (block) on: secrets, files > 20 MB, media/model files, nested repos.
Warns (does not block) when a new code file hard-codes this repo's own folder path (use Common/tools/gwpaths instead)."""
import re, subprocess, sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Common" / "tools"))
    import gwpaths  # noqa: E402
    NAME, ROOT = gwpaths.me()["workflow"], gwpaths.ROOT_FWD
except Exception:
    NAME, ROOT = "Workflow", Path(__file__).resolve().parents[2].as_posix()

MAX = 20 * 1024 * 1024
BLOCK_EXT = (".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".zip",
             ".7z", ".rar", ".exe", ".dll", ".msi", ".npy", ".npz", ".pt", ".pth", ".bin", ".onnx", ".safetensors",
             ".ckpt", ".gguf", ".psd")
MEDIA_OK = ()                          # folder prefixes whose media files may be committed, e.g. ("assets/sounds/",)
SECRET = re.compile(r"(sk-ant-[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9]{40,}|ghp_[A-Za-z0-9]{30,}|gho_[A-Za-z0-9]{30,}|"
                    r"github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_\-]{35}|xox[baprs]-[A-Za-z0-9\-]{10,}|"
                    r"nvapi-[A-Za-z0-9_\-]{20,}|gsk_[A-Za-z0-9]{20,}|mstrl_[A-Za-z0-9_\-]{20,}|sk-or-v1-[A-Za-z0-9]{20,}|"
                    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)")
CODE_EXT = (".py", ".mjs", ".js", ".ts", ".tsx", ".ps1", ".sh")
HARD = re.compile(r"[\\/]+".join(re.escape(part) for part in ROOT.split("/") if part), re.I)


def git(*a):
    return subprocess.run(["git", *a], capture_output=True).stdout


raw = git("diff", "--cached", "--raw", "-z", "--diff-filter=ACMR").split(b"\0")
problems, warns = [], []
i = 0
while i < len(raw) - 1:
    meta, path = raw[i].decode("utf-8", "replace"), raw[i + 1].decode("utf-8", "replace")
    i += 2
    if meta.startswith(":") and " R" in meta:      # rename has two paths
        path = raw[i].decode("utf-8", "replace"); i += 1
    mode = meta.split()[1] if meta.startswith(":") else ""
    if mode == "160000":
        problems.append(f"nested git repo: {path} (add it to .gitignore instead)")
        continue
    low = path.lower()
    if low.endswith(BLOCK_EXT) and not path.startswith(MEDIA_OK):
        problems.append(f"media/model file: {path} (media stays on each machine)")
        continue
    size = int((git("cat-file", "-s", f":{path}") or b"0").strip() or 0)
    if size > MAX:
        problems.append(f"file over 20 MB: {path} ({size / 1e6:.0f} MB)")
        continue
    if size < 3_000_000:
        blob = git("show", f":{path}")
        if b"\0" not in blob[:8000]:
            text = blob.decode("utf-8", "replace")
            if SECRET.search(text) and not path.endswith(("precommit_guard.py", "secrets.vault")):
                problems.append(f"looks like a SECRET (key/token/private key): {path}")
            if low.endswith(CODE_EXT) and HARD.search(text) and "gwpaths" not in text and meta.split()[4:5] == ["A"]:
                warns.append(f"hard-coded repo path ({ROOT}) in new code: {path} (use Common/tools/gwpaths)")

for w in warns:
    print("guard warning: " + w)
if problems:
    print(f"{NAME} guard BLOCKED this commit:")
    for p in problems:
        print("  - " + p)
    print("Fix: unstage the file (git restore --staged <file>) or add it to .gitignore. Nothing was pushed.")
    sys.exit(1)
