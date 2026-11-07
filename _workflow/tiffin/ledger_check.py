r"""ledger_check.py - mechanical gap finder between what the user SAID and what the LEDGER / handoff note holds.

Usage:
  python ledger_check.py <said.md> <ledger.md> [<handoff.md>] [--project <folder>]

For every user message in the said file it pulls out candidate "decision atoms":
  numbers with units (30 fps, 45 f, 27 cards/min), file-ish names (x.json, Film.tsx, comp ids), quoted words,
  and sentences with decision verbs (approve / no / never / always / instead / remove / keep / fix ...).
Then it checks whether each atom's key tokens appear in the ledger, the note, or (with --project) any .md/.json under docs/.
Prints the atoms that appear NOWHERE. These are the lines check-tiffin must judge (real decision or chatter?).
Exit code 0 always; the judgement belongs to the agent, this only makes sure nothing is overlooked.
"""
import os, re, sys, glob

DECIDE = re.compile(r"\b(approve|approved|ok|okay|yes|love|perfect|keep|lock|final|no|not|don'?t|never|always|instead|"
                    r"wrong|reject|hate|remove|change|fix|should|must|prefer|from now on|rule|remember|want)\b", re.I)
NUM = re.compile(r"\b\d+(?:\.\d+)?\s*(?:fps|s|sec|seconds|min|px|%|k|frames?|f|words?|cards?|lines?|gb|mb)\b", re.I)
FILEISH = re.compile(r"\b[\w-]+\.(?:json|tsx?|py|md|mp4|wav|mp3|png|jpg)\b|\b[A-Z][A-Za-z0-9]+-[A-Za-z0-9-]+\b")
STOP = set("the a an and or to of in on for with is are was be it this that i you we my me so but if then than as at by "
           "from not no yes do does did have has had can could should would will just like want make made get got".split())


def read(p):
    return open(p, encoding="utf-8", errors="replace").read() if p and os.path.exists(p) else ""


def messages(said):
    return [m.strip() for m in re.split(r"\n## \d+\. [\d -:]+\n", said)[1:] if m.strip()]


def atoms(msg):
    out = set()
    for s in re.split(r"(?<=[.!?\n])\s+", msg):
        s = s.strip()
        if len(s) < 6:
            continue
        if DECIDE.search(s) or NUM.search(s) or FILEISH.search(s):
            out.add(s[:160])
    return out


def key_tokens(atom):
    toks = set(t.lower() for t in re.findall(r"[A-Za-z][\w'-]{2,}|\d+(?:\.\d+)?", atom))
    return [t for t in toks if t not in STOP]


def covered(atom, haystack):
    toks = key_tokens(atom)
    if not toks:
        return True
    hits = sum(1 for t in toks if t in haystack)
    return hits / len(toks) >= 0.6


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    a = sys.argv[1:]
    proj = None
    if "--project" in a:
        i = a.index("--project"); proj = a[i + 1]; del a[i:i + 2]
    if len(a) < 2:
        sys.exit(__doc__)
    said, ledger = read(a[0]), read(a[1])
    note = read(a[2]) if len(a) > 2 else ""
    extra = ""
    if proj:
        for f in glob.glob(os.path.join(proj, "docs", "**", "*.*"), recursive=True):
            if f.lower().endswith((".md", ".json", ".txt")) and os.path.getsize(f) < 400_000:
                extra += read(f).lower()
    hay = (ledger + "\n" + note).lower() + extra
    total = missing = 0
    print(f"# ledger_check: {os.path.basename(a[0])} vs ledger{' + note' if note else ''}{' + docs/' if proj else ''}\n")
    for n, msg in enumerate(messages(said), 1):
        gaps = [at for at in sorted(atoms(msg)) if not covered(at, hay)]
        total += len(atoms(msg)); missing += len(gaps)
        for g in gaps:
            print(f"- msg {n}: {g}")
    print(f"\n{total} decision-like sentences, {missing} not found anywhere. "
          "Each line above is either a real lost decision (add to the ledger) or chatter (ignore).")


if __name__ == "__main__":
    main()
