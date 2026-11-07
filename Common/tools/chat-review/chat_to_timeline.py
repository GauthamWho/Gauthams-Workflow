"""Turn a Claude Code session transcript (.jsonl) into a short, readable timeline.

Keeps: every user message (full), assistant text (trimmed), one line per tool call.
Drops: tool results, system reminders, thinking, hook noise.

Usage:
  python chat_to_timeline.py <session.jsonl> [out.md] [--text-limit 700]
  python chat_to_timeline.py --find <cli-session-id>      # print the .jsonl path for an id

Each user turn is numbered U1, U2 ... so findings can cite "U14" and the timestamp.
"""
import json, re, sys, os, glob

PROJECTS = os.path.expanduser("~/.claude/projects")
NOISE = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
SYSTEM_MSG = ("<task-notification", "<agent-message", "<side-sessions-event", "<ci-monitor-event", "/auto-mode-setup")
PASTE_ID = re.compile(r'<pasted_content id="[^"]*">|</pasted_content[^>]*>')


def find(session_id):
    hits = glob.glob(os.path.join(PROJECTS, "*", session_id + "*.jsonl"))
    return hits[0] if hits else None


def text_of(content):
    if isinstance(content, str):
        return content, 0
    out, images = [], 0
    for c in content or []:
        if not isinstance(c, dict):
            continue
        if c.get("type") == "text":
            out.append(c.get("text", ""))
        elif c.get("type") == "image":
            images += 1
    return "\n".join(out), images


def tool_line(c):
    name = c.get("name", "?")
    inp = c.get("input") or {}
    key = (inp.get("description") or inp.get("file_path") or inp.get("command")
           or inp.get("pattern") or inp.get("prompt") or inp.get("url") or inp.get("skill") or "")
    key = str(key).replace("\n", " ")[:140]
    return f"  - `{name}` {key}"


def clean(path, limit=700):
    lines, u, seen = [], 0, set()
    for raw in open(path, encoding="utf-8", errors="replace"):
        try:
            d = json.loads(raw)
        except Exception:
            continue
        t, ts = d.get("type"), (d.get("timestamp") or "")[:16].replace("T", " ")
        msg = d.get("message") or {}
        if t == "queue-operation" and d.get("operation") == "enqueue":
            # a message typed while Claude was busy (or sent by another session)
            txt = d.get("content")
            txt = txt if isinstance(txt, str) else text_of(txt)[0]
            txt = PASTE_ID.sub("", NOISE.sub("", txt or "")).strip()
            if not txt or txt.startswith(SYSTEM_MSG) or txt in seen:
                continue
            seen.add(txt)
            if txt.startswith("<cross-session-message"):
                m = re.search(r'from-name="([^"]*)"', txt)
                body = re.sub(r"<[^>]+>", "", txt).strip()[:limit]
                lines.append(f"\n[{ts}] (message from session '{m.group(1) if m else '?'}') {body}")
                continue
            u += 1
            lines.append(f"\n### U{u} [{ts}] (sent while Claude was busy)\n{txt}\n")
            continue
        if t == "user":
            content = msg.get("content")
            if isinstance(content, list) and any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
                continue  # tool output, not the user speaking
            txt, imgs = text_of(content)
            txt = PASTE_ID.sub("", NOISE.sub("", txt)).strip()
            if d.get("isMeta") or (not txt and not imgs) or txt.startswith(SYSTEM_MSG):
                continue
            if txt.startswith("This session is being continued"):
                lines.append(f"\n---- [{ts}] CONTEXT COMPACTED (summary skipped) ----\n")
                continue
            if "<local-command-stdout>" in txt or "<command-name>" in txt and len(txt) < 300:
                lines.append(f"\n[{ts}] (slash command) {txt[:200]}")
                continue
            if txt in seen:
                continue  # queued message delivered later as a normal turn
            seen.add(txt)
            u += 1
            tag = f" [+{imgs} image]" if imgs else ""
            lines.append(f"\n### U{u} [{ts}]{tag}\n{txt}\n")
        elif t == "assistant":
            for c in msg.get("content") or []:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "text" and c.get("text", "").strip():
                    s = c["text"].strip()
                    if len(s) > limit:
                        s = s[:limit] + " …[trimmed]"
                    lines.append(f"**A:** {s}")
                elif c.get("type") == "tool_use":
                    lines.append(tool_line(c))
    return "\n".join(lines), u


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--find":
        print(find(args[1]) or "not found")
        sys.exit()
    limit = 700
    if "--text-limit" in args:
        i = args.index("--text-limit"); limit = int(args[i + 1]); del args[i:i + 2]
    src = args[0] if os.path.exists(args[0]) else find(args[0])
    body, n = clean(src, limit)
    out = args[1] if len(args) > 1 else None
    head = f"# Timeline: {os.path.basename(src)}\nUser turns: {n}\n"
    if out:
        open(out, "w", encoding="utf-8").write(head + body)
        print(f"{out}  ({n} user turns, {len(body)//1000} KB)")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(head + body)
