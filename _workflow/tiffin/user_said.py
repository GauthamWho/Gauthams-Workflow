r"""user_said.py - the lossless layer of the Tiffin box.

Dumps EVERY message the user typed in a chat, verbatim and timestamped, to a markdown file,
and Claude's own replies to a second file (<same>.claude.md) so the next chat keeps the WHY behind each choice.
A summary can forget; this cannot. The checker (check-tiffin) and the next chat read it.

Usage:
  python user_said.py <transcript.jsonl | session-id | --current> [--out <file>] [--since <ISO time>]
  --current  = the newest transcript under ~/.claude/projects for the current folder (cwd).
Default --out: <repo>/_claude/handoffs/said/<yyyy-mm-dd>_<session8>.md

Keeps, in time order: typed messages; messages typed while Claude was working (queued_command attachments
with origin human; task notifications, agent hand-backs and peer/session messages are skipped); answers and
notes typed into a question box (AskUserQuestion results); the reason typed when rejecting a tool call.
Skips other tool results, slash-command echoes, hook/system text and pasted-file wrappers.
Keeps <pasted_content> text (the user pasted it on purpose). Redacts obvious secrets.
"""
import json, os, re, sys, glob
from datetime import datetime

HOME = os.path.expanduser("~")
PROJECTS = os.path.join(HOME, ".claude", "projects")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "Common", "tools"))
    from gwpaths import ROOT  # type: ignore
    GW_HOME = str(ROOT)
except Exception:
    GW_HOME = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

NOISE = ("<local-command-caveat>", "<command-name>", "<command-message>", "<local-command-stdout>", "<system-reminder>",
         "[Request interrupted", "<task-notification>", "<side-sessions-event>", "<ci-monitor-event>",
         "Another Claude session sent a message", "<agent-message", "[Image:", "Base directory for this skill",
         "This session is being continued from a previous conversation")
# the continuation summary is Claude's text, not the user's; agent messages and skill bodies likewise
SECRET = re.compile(r"(sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}|xox[a-z]-[A-Za-z0-9-]{10,}|"
                    r"[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]\s*[:=]\s*\S{6,}|(?:[Tt]oken|[Pp]assword|[Ss]ecret)\s*[:=]\s*\S{6,})")


def find_transcript(arg):
    if arg == "--current":
        key = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd())
        files = glob.glob(os.path.join(PROJECTS, key, "*.jsonl"))
        if not files:
            sys.exit(f"no transcript for {os.getcwd()}")
        return max(files, key=os.path.getmtime)
    if os.path.exists(arg):
        return arg
    hits = glob.glob(os.path.join(PROJECTS, "*", f"{arg}*.jsonl"))
    if not hits:
        sys.exit(f"no transcript matches {arg}")
    return hits[0]


def text_of(content):
    if isinstance(content, str):
        return content
    parts = []
    for b in content or []:
        if isinstance(b, dict) and b.get("type") == "text":
            parts.append(b.get("text", ""))
    return "\n".join(parts)


def clean(txt):
    txt = re.sub(r"<system-reminder>.*?</system-reminder>", "", txt, flags=re.S)
    txt = re.sub(r"<pasted_content id=\"[^\"]*\">", "[pasted]\n", txt)
    txt = re.sub(r"</pasted_content id=\"[^\"]*\">", "\n[/pasted]", txt)
    txt = SECRET.sub("[redacted]", txt)
    return txt.strip()


ANSWER_HEADS = ("The user answered:", "Your questions have been answered:", "User has answered your questions:")
REJECT_SAID = "the user said:"


def _fmt_answer(v):
    return ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)


def question_box(e, c):
    """Text the user gave in a question box (AskUserQuestion), or None."""
    tur = e.get("toolUseResult")
    if isinstance(tur, dict) and isinstance(tur.get("answers"), dict) and "questions" in tur:
        lines = []
        notes = tur.get("annotations") if isinstance(tur.get("annotations"), dict) else {}
        for q, a in tur["answers"].items():
            if "[User did not answer this question" in _fmt_answer(a):
                continue  # the user typed a message instead; that message is kept on its own
            lines.append(f"Q: {q}\nA: {_fmt_answer(a)}")
            n = (notes.get(q) or {}).get("notes") if isinstance(notes.get(q), dict) else None
            if n:
                lines.append(f"Notes: {n}")
        return "[question box]\n" + "\n\n".join(lines) if lines else None
    for b in c:  # older transcripts without toolUseResult: fall back to the tool_result text
        if isinstance(b, dict) and b.get("type") == "tool_result":
            t = text_of(b.get("content")) if not isinstance(b.get("content"), str) else b["content"]
            if t.lstrip().startswith(ANSWER_HEADS):
                t = re.sub(r"\s*You can now continue with (these|the user's) answers in mind\.?\s*$", "", t.strip())
                return "[question box]\n" + t
    return None


def rejection_reason(c):
    """The words the user typed when rejecting a tool call, or None."""
    for b in c:
        if isinstance(b, dict) and b.get("type") == "tool_result":
            t = text_of(b.get("content")) if not isinstance(b.get("content"), str) else b["content"]
            if t.startswith("The user doesn't want to proceed") and REJECT_SAID in t.lower():
                i = t.lower().index(REJECT_SAID) + len(REJECT_SAID)
                said = t[i:].strip()
                if said:
                    return "[rejected a tool call] " + said
    return None


def user_entry(e):
    """(ts, raw text) if this transcript line carries words the user typed, else None."""
    if e.get("isSidechain"):
        return None
    ts = e.get("timestamp", "")
    a = e.get("attachment")
    if e.get("type") == "attachment" and isinstance(a, dict) and a.get("type") == "queued_command":
        if a.get("commandMode") != "prompt" or (a.get("origin") or {}).get("kind", "human") != "human":
            return None  # task notifications, agent hand-backs, peer sessions
        txt = text_of(a.get("prompt"))
        if not txt.strip() or any(x in txt.lstrip()[:80] for x in NOISE):
            return None
        return (a.get("timestamp") or ts, "[typed while Claude was working] " + txt, a.get("source_uuid"))
    if e.get("type") != "user":
        return None
    c = (e.get("message") or {}).get("content")
    if isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
        t = question_box(e, c) or rejection_reason(c)
        return (ts, t, None) if t else None
    txt = text_of(c)
    if not txt.strip() or any(x in txt.lstrip()[:80] for x in NOISE):
        return None
    return (ts, txt, None)


def _entries(path):
    seen_q, seen_txt = set(), {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            try:
                e = json.loads(raw)
            except Exception:
                continue
            u = user_entry(e)
            if u is None:
                yield e, None
                continue
            ts, txt, qid = u
            if qid:  # a queued message is attached once per delivery; keep one copy
                if qid in seen_q:
                    yield e, None
                    continue
                seen_q.add(qid)
            key = re.sub(r"^\[typed while Claude was working\] ", "", txt).strip()
            if key in seen_txt and abs(_secs(ts) - _secs(seen_txt[key])) < 600:
                yield e, None  # the same words also arrived as a normal turn
                continue
            seen_txt[key] = ts
            yield e, (ts, txt)


def _secs(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0


def claude_messages(path, since=None):
    """Claude's own words (text blocks only; tool calls and results stay on disk). Each item: (ts, after_user_n, text)."""
    out, n = [], 0
    for e, u in _entries(path):
        if u is not None:
            if clean(u[1]):
                n += 1
            continue
        if e.get("isSidechain") or e.get("type") != "assistant":
            continue
        txt = text_of((e.get("message") or {}).get("content"))
        txt = SECRET.sub("[redacted]", txt).strip()
        if len(txt) < 20:
            continue
        ts = e.get("timestamp", "")
        if since and ts < since:
            continue
        out.append((ts, n, txt))
    return out


def user_messages(path, since=None):
    out = []
    for e, u in _entries(path):
        if u is None:
            continue
        ts, txt = u
        txt = clean(txt)
        if not txt:
            continue
        if since and ts < since:
            continue
        out.append((ts, txt))
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    out = None
    since = None
    if "--out" in args:
        i = args.index("--out"); out = args[i + 1]; del args[i:i + 2]
    if "--since" in args:
        i = args.index("--since"); since = args[i + 1]; del args[i:i + 2]
    path = find_transcript(args[0])
    sid = os.path.basename(path)[:8]
    msgs = user_messages(path, since)
    if not out:
        day = (msgs[0][0][:10] if msgs else datetime.now().strftime("%Y-%m-%d"))
        out = os.path.join(GW_HOME, "_claude", "handoffs", "said", f"{day}_{sid}.md")
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# What the user said - session {sid}\n\n")
        f.write(f"Source: `{path}`  \nMessages: {len(msgs)}. Verbatim; nothing summarised. "
                "Every approve / reject / number / preference in here must appear in the project LEDGER.md.\n\n")
        for n, (ts, txt) in enumerate(msgs, 1):
            t = ts.replace("T", " ")[:16]
            f.write(f"## {n}. {t}\n\n{txt}\n\n")
    print(out)
    print(f"{len(msgs)} user messages")
    # second file: what Claude said (its choices and reasons), so the next chat does not repeat dead ends
    cl = claude_messages(path, since)
    cout = out[:-3] + ".claude.md" if out.endswith(".md") else out + ".claude.md"
    with open(cout, "w", encoding="utf-8") as f:
        f.write(f"# What Claude said - session {sid}\n\n")
        f.write(f"Source: `{path}`  \nBlocks: {len(cl)}. Claude's own replies, verbatim (tool calls and results are not here; "
                "they live on disk). 'after user N' points at the user message in the said file it answers. "
                "Use it for the WHY behind a choice and for dead ends already tried; the user's decisions are in the said file + LEDGER.\n\n")
        for k, (ts, n, txt) in enumerate(cl, 1):
            f.write(f"## {k}. {ts.replace('T', ' ')[:16]} (after user {n})\n\n{txt}\n\n")
    print(cout)
    print(f"{len(cl)} Claude blocks")


if __name__ == "__main__":
    main()
