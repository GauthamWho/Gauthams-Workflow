"""Export every Claude Code chat on this machine as a readable "fair copy" into the repo,
so the other machine (Mac/PC) can read any chat by its exact title and continue the work.

  python export_chats.py            # writes <repo>/_claude/chats/  (+ CHATS.md index)

- One file per chat: <machine>/<date>_<title>_<id8>.md (only rewritten when the chat changed).
- Secrets (tokens, keys, passwords) are masked before writing.
- Raw transcripts (.jsonl) are NOT copied: too big and full of tool output.
"""
import json, os, re, sys, glob, platform

sys.path.insert(0, os.path.dirname(__file__))
from chat_to_timeline import clean  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))          # the repo root
OUT = os.path.join(ROOT, "_claude", "chats")
MACHINE = "mac" if platform.system() == "Darwin" else "pc"
PROJECTS = os.path.expanduser("~/.claude/projects")

SECRETS = [
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b"), "[BOT-TOKEN]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), "[API-KEY]"),
    (re.compile(r"\b(ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}"), "[GITHUB-TOKEN]"),
    (re.compile(r"\bnvapi-[A-Za-z0-9_-]{20,}"), "[NVIDIA-KEY]"),
    (re.compile(r"\bgsk_[A-Za-z0-9]{20,}"), "[GROQ-KEY]"),
    (re.compile(r"\bmstrl_[A-Za-z0-9_-]{20,}"), "[MISTRAL-KEY]"),
    (re.compile(r"\b(hf|r8|glpat|xai|pplx)[_-][A-Za-z0-9_-]{20,}"), "[API-KEY]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[AWS-KEY]"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "[GOOGLE-KEY]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "[SLACK-TOKEN]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{20,}"), "Bearer [TOKEN]"),
    (re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd)(\"?\s*[:=]\s*\"?)[^\s\"',]{6,}"), r"\1\2[HIDDEN]"),
]


def redact(s):
    for rx, rep in SECRETS:
        s = rx.sub(rep, s)
    return s


def meta(path):
    title, cwd, first, last = None, None, None, None
    for raw in open(path, encoding="utf-8", errors="replace"):
        if '"customTitle"' in raw:
            m = re.search(r'"customTitle":"((?:[^"\\]|\\.)*)"', raw)
            if m:
                title = json.loads('"' + m.group(1) + '"')
        if cwd is None and '"cwd"' in raw:
            m = re.search(r'"cwd":"((?:[^"\\]|\\.)*)"', raw)
            if m:
                cwd = json.loads('"' + m.group(1) + '"')
        m = re.search(r'"timestamp":"([^"]+)"', raw)
        if m:
            first = first or m.group(1)
            last = m.group(1)
    return title, cwd, first, last


def safe(s):
    s = re.sub(r"[^\w\- ]+", "", s, flags=re.UNICODE).strip().replace(" ", "-")
    return s[:60] or "untitled"


def main():
    os.makedirs(os.path.join(OUT, MACHINE), exist_ok=True)
    rows, cache_p = [], os.path.join(OUT, f".cache-{MACHINE}.json")
    cache = json.load(open(cache_p, encoding="utf-8")) if os.path.exists(cache_p) else {}
    for path in sorted(glob.glob(os.path.join(PROJECTS, "*", "*.jsonl"))):
        sid = os.path.basename(path)[:-6]
        mt = os.path.getmtime(path)
        c = cache.get(sid)
        if c and c["mtime"] == mt and os.path.exists(os.path.join(OUT, c["rel"])):
            rows.append(tuple(c["row"]))  # unchanged since last export: skip reading the big file
            continue
        title, cwd, first, last = meta(path)
        if not first:
            continue
        title = title or "(untitled)"
        name = f"{first[:10]}_{safe(title)}_{sid[:8]}.md"
        dest = os.path.join(OUT, MACHINE, name)
        stamp = f"<!-- last:{last} -->"
        if not (os.path.exists(dest) and stamp in open(dest, encoding="utf-8").read(400)):
            body, turns = clean(path)
            head = (f"{stamp}\n# {title}\n\n"
                    f"- Chat id: `{sid}` ({MACHINE})\n- Folder: `{cwd}`\n"
                    f"- From {first[:16].replace('T', ' ')} to {last[:16].replace('T', ' ')} UTC, {turns} user turns\n"
                    f"- Fair copy (clean timeline): your messages in full, Claude's replies trimmed, one line per tool call.\n"
                    f"  To continue this work on another machine, open a chat in the same folder and say:\n"
                    f"  \"read _claude/chats/{MACHINE}/{name} and continue from where it stopped\".\n")
            open(dest, "w", encoding="utf-8").write(redact(head + body))
        rows.append((last, title, cwd, f"{MACHINE}/{name}", first))
        cache[sid] = {"mtime": mt, "rel": f"{MACHINE}/{name}", "row": rows[-1]}
    # index for this machine
    rows.sort(reverse=True)
    idx = [f"# Chats on the {MACHINE.upper()} (newest first)\n",
           "Exported by `Common/tools/chat-review/export_chats.py` (runs on every sync). Open the file to read the chat.\n",
           "| Last active (UTC) | Chat title | Folder | Fair copy |", "|---|---|---|---|"]
    for last, title, cwd, rel, first in rows:
        idx.append(f"| {last[:16].replace('T', ' ')} | {title.replace('|', '/')} | `{cwd}` | [{os.path.basename(rel)}]({rel}) |")
    open(os.path.join(OUT, f"CHATS-{MACHINE}.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")
    json.dump(cache, open(cache_p, "w", encoding="utf-8"))
    print(f"{len(rows)} chats -> {OUT}")


if __name__ == "__main__":
    main()
