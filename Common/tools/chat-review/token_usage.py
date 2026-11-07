"""Token use per chat on this machine (Windows PC or Mac), from the raw Claude Code transcripts.

  python token_usage.py                                   # today 00:00 -> now (IST)
  python token_usage.py --since "2026-11-06 00:00" --until "2026-11-06 16:15"
  python token_usage.py --compare                         # also merge the other machine's USAGE file

Writes _claude/chats/USAGE-<pc|mac>.md (+ .json) so the other machine sees it after a sync.
Counts every assistant reply once (streamed duplicates removed), subagent turns added to their chat.
Columns: fresh input, cache write, cache read, output. "Total" = all four added.
No cost figures (tokens only).
"""
import argparse, glob, json, os, platform, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "_claude", "chats")
MACHINE = "mac" if platform.system() == "Darwin" else "pc"
PROJECTS = os.path.expanduser("~/.claude/projects")


def parse_local(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=IST)


def scan(since, until):
    chats = {}
    files = glob.glob(os.path.join(PROJECTS, "*", "*.jsonl")) + \
        glob.glob(os.path.join(PROJECTS, "*", "*", "subagents", "*.jsonl"))
    for path in files:
        parts = os.path.normpath(path).split(os.sep)
        sid = parts[-3] if parts[-2] == "subagents" else os.path.basename(path)[:-6]
        c = chats.setdefault(sid, {"title": None, "cwd": None, "inp": 0, "cw": 0, "cr": 0, "out": 0,
                                   "turns": 0, "models": {}, "last": None})
        seen = set()
        for raw in open(path, encoding="utf-8", errors="replace"):
            if '"customTitle"' in raw and parts[-2] != "subagents":
                m = re.search(r'"customTitle":"((?:[^"\\]|\\.)*)"', raw)
                if m:
                    c["title"] = json.loads('"' + m.group(1) + '"')
            if '"usage"' not in raw:
                if c["cwd"] is None and '"cwd"' in raw:
                    m = re.search(r'"cwd":"((?:[^"\\]|\\.)*)"', raw)
                    if m:
                        c["cwd"] = json.loads('"' + m.group(1) + '"')
                continue
            try:
                e = json.loads(raw)
            except Exception:
                continue
            if c["cwd"] is None:
                c["cwd"] = e.get("cwd")
            msg = e.get("message") or {}
            u = msg.get("usage")
            ts = e.get("timestamp")
            if e.get("type") != "assistant" or not u or not ts:
                continue
            t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if not (since <= t <= until):
                continue
            key = (msg.get("id"), e.get("requestId"))
            if key in seen:
                continue
            seen.add(key)
            c["inp"] += u.get("input_tokens", 0) or 0
            c["cw"] += u.get("cache_creation_input_tokens", 0) or 0
            c["cr"] += u.get("cache_read_input_tokens", 0) or 0
            c["out"] += u.get("output_tokens", 0) or 0
            c["turns"] += 1
            mdl = msg.get("model", "?")
            c["models"][mdl] = c["models"].get(mdl, 0) + 1
            c["last"] = max(c["last"] or ts, ts)
    rows = []
    for sid, c in chats.items():
        if not c["turns"]:
            continue
        c["total"] = c["inp"] + c["cw"] + c["cr"] + c["out"]
        c["sid"] = sid
        c["machine"] = MACHINE
        c["title"] = c["title"] or f"(untitled {sid[:8]})"
        rows.append(c)
    rows.sort(key=lambda r: -r["total"])
    return rows


def fmt(n):
    return f"{n/1e6:.1f}M" if n >= 1e6 else f"{n/1e3:.0f}k"


def table(rows, with_machine=False):
    head = "| # | " + ("Machine | " if with_machine else "") + \
        "Chat | Total | Output | Fresh in | Cache write | Cache read | Replies |"
    lines = [head, "|" + "---|" * (head.count("|") - 1)]
    for i, r in enumerate(rows, 1):
        lines.append(f"| {i} | " + (f"{r['machine']} | " if with_machine else "") +
                     f"{r['title'].replace('|', '/')} | **{fmt(r['total'])}** | {fmt(r['out'])} | "
                     f"{fmt(r['inp'])} | {fmt(r['cw'])} | {fmt(r['cr'])} | {r['turns']} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    now = datetime.now(IST)
    ap.add_argument("--since", default=now.strftime("%Y-%m-%d 00:00"))
    ap.add_argument("--until", default=now.strftime("%Y-%m-%d %H:%M"))
    ap.add_argument("--compare", action="store_true")
    a = ap.parse_args()
    since, until = parse_local(a.since), parse_local(a.until)
    rows = scan(since, until)
    os.makedirs(OUT, exist_ok=True)
    json.dump({"since": a.since, "until": a.until, "rows": rows},
              open(os.path.join(OUT, f"USAGE-{MACHINE}.json"), "w", encoding="utf-8"), indent=1)
    tot = sum(r["total"] for r in rows)
    md = [f"# Token use per chat ({MACHINE}), {a.since} -> {a.until} IST", "",
          f"{len(rows)} chats, {fmt(tot)} tokens in all.", "", table(rows)]
    if a.compare:
        other = os.path.join(OUT, f"USAGE-{'pc' if MACHINE == 'mac' else 'mac'}.json")
        if os.path.exists(other):
            o = json.load(open(other, encoding="utf-8"))
            allr = sorted(rows + o["rows"], key=lambda r: -r["total"])
            md += ["", f"## Both machines (other machine's window: {o['since']} -> {o['until']})", "",
                   table(allr, True)]
        else:
            md += ["", "Other machine has no USAGE file yet: run this script there and sync."]
    open(os.path.join(OUT, f"USAGE-{MACHINE}.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
