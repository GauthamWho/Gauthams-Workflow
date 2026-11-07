"""Phone check: prove a local page really answers on the Wi-Fi address BEFORE giving the user the phone link.

  python Common/tools/lan/phonecheck.py <port> [path]     e.g. phonecheck.py 8813 /index.html

PASS -> prints both links (PC + phone); give them to the user.
FAIL -> the server only listens on this PC (e.g. started from inside the Claude app, which can sandbox it to
        127.0.0.1) or isn't running. Do NOT give the phone link; tell the user and give a double-click launcher
        or restart the server with host 0.0.0.0 outside the sandbox.
Exit code 0 = PASS, 1 = FAIL. Born from a chat review (Bigg Boss): 5 broken phone links in 3 chats.
"""
import sys, os, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serve import wifi_ip  # noqa: E402


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=4) as r:
            return r.status, r.headers.get("Cache-Control", "")
    except Exception as e:  # refused, timeout, 404 ...
        return None, str(e)[:120]


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    port = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else "/"
    path = path if path.startswith("/") else "/" + path
    ip = wifi_ip()
    pc, phone = f"http://localhost:{port}{path}", f"http://{ip}:{port}{path}"
    s_pc, _ = fetch(pc)
    s_ph, info = fetch(phone)
    if s_ph and s_ph < 400:
        print(f"PASS  phone address answers ({s_ph}).")
        print(f"  This PC: {pc}\n  Phone (same Wi-Fi): {phone}")
        if "no-cache" not in info.lower():
            print("  note: no 'no-cache' header - if the phone shows an old version, tell the user to reload.")
        return 0
    why = ("the server is running but only on this PC (bound to 127.0.0.1 / sandboxed)" if s_pc and s_pc < 400
           else "nothing answers on this port - the server isn't running")
    print(f"FAIL  {phone} does not answer: {why}. ({info})")
    print("  Don't give the phone link. Give the PC link, and a launcher the user double-clicks (runs outside Claude).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
