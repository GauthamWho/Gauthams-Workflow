"""add_copybar.py <page.html> [...]: inline copybar.js (sticky top bar + Copy button for the "copy this into the chat"
line) into each page, right before </body>. Idempotent: an older inlined copy is replaced. User rule 2026-11-07."""
import re, sys, pathlib
JS = (pathlib.Path(__file__).parent / "copybar.js").read_text(encoding="utf-8")
BLOCK = "<!--copybar--><script>\n" + JS + "</script><!--/copybar-->"
for a in sys.argv[1:]:
    p = pathlib.Path(a); s = p.read_text(encoding="utf-8")
    s = re.sub(r"<!--copybar-->.*?<!--/copybar-->", "", s, flags=re.S)
    s = s.replace("</body>", BLOCK + "</body>", 1) if "</body>" in s else s + BLOCK
    p.write_text(s, encoding="utf-8"); print("copybar ->", p)
