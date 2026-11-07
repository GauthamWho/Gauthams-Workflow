r"""vault.py - the secrets vault INSIDE the repo (keys travel with the workflow).

Ships EMPTY: list the env vars you want to carry in ENV_NAMES and the config files in FILES below.

One encrypted file `_workflow/secrets.vault` (AES via `cryptography` Fernet, key from a passphrase with PBKDF2, 600k rounds).
Plaintext never touches git: the guard still blocks keys in any other file.

  python vault.py lock              collect the secrets listed in ENV_NAMES / FILES from this machine (env vars + files), encrypt, write the vault
  python vault.py unlock --env      set the env vars on this machine (Windows: setx; Mac: appends to ~/.zshrc)
  python vault.py unlock --files    restore the config files listed in FILES to their paths
  python vault.py list              show the NAMES stored in the vault (never the values)
  python vault.py add NAME          add or replace one env secret (prompts for the value, hidden)

The passphrase is asked each time (or read from env GW_VAULT_PASS for scripts). Lose the passphrase = lose the vault; keep a
note of each name and where to re-issue the key, so the workflow can always be rebuilt by hand.
The vault file is created by the first `lock` or `add`; until then there is nothing to unlock.
"""
import base64, getpass, json, os, platform, subprocess, sys
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    sys.exit("pip install cryptography")

HERE = Path(__file__).resolve().parent
VAULT = HERE / "secrets.vault"
HOME = Path.home()

ENV_NAMES = []  # e.g. ["OPENROUTER_API_KEY", "HF_TOKEN"]
# files: vault name -> path on this machine (same on the Mac with ~)
FILES = {
    # e.g. "opencode.jsonc": HOME / ".config" / "opencode" / "opencode.jsonc",
}
SALT = b"workflow-vault-v1"


def key(passphrase):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=600_000)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def passphrase(confirm=False):
    p = os.environ.get("GW_VAULT_PASS") or getpass.getpass("vault passphrase: ")
    if confirm and not os.environ.get("GW_VAULT_PASS"):
        if getpass.getpass("again: ") != p:
            sys.exit("passphrases differ")
    return p


def read_vault(p):
    if not VAULT.exists():
        return {"env": {}, "files": {}}
    try:
        return json.loads(Fernet(key(p)).decrypt(VAULT.read_bytes()))
    except Exception:
        sys.exit("wrong passphrase (or damaged vault)")


def write_vault(p, data):
    VAULT.write_bytes(Fernet(key(p)).encrypt(json.dumps(data).encode()))
    print(f"vault written: {VAULT}  ({len(data['env'])} env, {len(data['files'])} files)")


def cmd_lock():
    p = passphrase(confirm=not VAULT.exists())
    data = read_vault(p) if VAULT.exists() else {"env": {}, "files": {}}
    found = []
    for n in ENV_NAMES:
        v = os.environ.get(n)
        if v:
            data["env"][n] = v; found.append(n)
    for n, path in FILES.items():
        if path.exists():
            data["files"][n] = {"path": str(path).replace(str(HOME), "~"), "text": path.read_text(encoding="utf-8", errors="replace")}
            found.append(n)
    write_vault(p, data)
    print("stored:", ", ".join(found) or "nothing found on this machine")
    missing = [n for n in ENV_NAMES if n not in data["env"]]
    if missing:
        print("not set here (add with `vault.py add NAME` if you have them):", ", ".join(missing))


def cmd_unlock(env, files):
    if not VAULT.exists():
        sys.exit(f"no vault yet ({VAULT}); create it with `vault.py lock` or `vault.py add NAME`")
    p = passphrase()
    data = read_vault(p)
    if env:
        for n, v in data["env"].items():
            os.environ[n] = v
            if platform.system() == "Windows":
                subprocess.run(["setx", n, v], capture_output=True)
            else:
                rc = HOME / ".zshrc"
                line = f'export {n}="{v}"\n'
                txt = rc.read_text() if rc.exists() else ""
                if f"export {n}=" not in txt:
                    rc.write_text(txt + line)
        print(f"{len(data['env'])} env vars set:", ", ".join(data["env"]))
    if files:
        for n, f in data["files"].items():
            path = Path(f["path"].replace("~", str(HOME)))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f["text"], encoding="utf-8")
            print("restored", path)


def cmd_list():
    if not VAULT.exists():
        sys.exit(f"no vault yet ({VAULT}); create it with `vault.py lock` or `vault.py add NAME`")
    p = passphrase()
    d = read_vault(p)
    print("env:", ", ".join(d["env"]) or "-")
    print("files:", ", ".join(f"{n} -> {f['path']}" for n, f in d["files"].items()) or "-")


def cmd_add(name):
    p = passphrase(confirm=not VAULT.exists())
    d = read_vault(p)
    d["env"][name] = getpass.getpass(f"value for {name}: ")
    write_vault(p, d)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "lock":
        cmd_lock()
    elif a[0] == "unlock":
        cmd_unlock("--env" in a, "--files" in a)
    elif a[0] == "list":
        cmd_list()
    elif a[0] == "add" and len(a) > 1:
        cmd_add(a[1])
    else:
        sys.exit(__doc__)
