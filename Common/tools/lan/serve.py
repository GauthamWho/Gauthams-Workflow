"""Phone-ready static server: reachable from devices on the same Wi-Fi, supports video seeking (HTTP Range).
Usage: python Common/tools/lan/serve.py <folder> [port=8800] [--local]
Prints the localhost link and the phone link (http://<PC Wi-Fi IP>:<port>/)."""
import os, re, socket, sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def wifi_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())
    finally:
        s.close()


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # Safari streams video more reliably over keep-alive

    def send_head(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        size = os.path.getsize(path)
        start = int(m.group(1)) if m and m.group(1) else 0
        end = min(int(m.group(2)) if m and m.group(2) else size - 1, size - 1)
        if start > end:
            self.send_error(416)
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        rem = getattr(self, "_remaining", None)
        if rem is None:
            return super().copyfile(source, outputfile)
        while rem > 0:
            buf = source.read(min(65536, rem))
            if not buf:
                break
            try:
                outputfile.write(buf)
            except (BrokenPipeError, ConnectionResetError):
                break
            rem -= len(buf)
        self._remaining = None

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")  # phones always get the latest page
        super().end_headers()

    def do_POST(self):
        """Pickers save picks here so the user never has to copy/paste: POST /_save/<name>.json (JSON body, <= 1 MB)
        is written to <served folder>/_picks/<name>.json. Nothing else can be written."""
        import json
        m = re.fullmatch(r"/_save/([A-Za-z0-9._-]{1,80})\.json", self.path.split("?")[0])
        n = int(self.headers.get("Content-Length") or 0)
        if not m or n <= 0 or n > 1_000_000:
            self.send_error(400, "bad save"); return
        body = self.rfile.read(n)
        try:
            json.loads(body)
        except ValueError:
            self.send_error(400, "not json"); return
        out = os.path.join(self.directory, "_picks"); os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, m.group(1) + ".json"), "wb") as f:
            f.write(body)
        # Content-Length is required: on HTTP/1.1 keep-alive the client otherwise waits forever for the reply to end
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", "14"); self.end_headers()
        self.wfile.write(b'{"saved":true}')

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = args[0] if args else "."
    port = int(args[1]) if len(args) > 1 else 8800
    host = "127.0.0.1" if "--local" in sys.argv else "0.0.0.0"
    srv = ThreadingHTTPServer((host, port), partial(Handler, directory=root))
    print(f"This PC: http://localhost:{port}/", flush=True)
    if host == "0.0.0.0":
        print(f"Phone (same Wi-Fi): http://{wifi_ip()}:{port}/", flush=True)
    srv.serve_forever()
