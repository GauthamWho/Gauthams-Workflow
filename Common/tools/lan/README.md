# Phone links (Common/tools/lan)

The rule lives in the workspace `CLAUDE.md` (every local page opens on the user's phone too). This file holds the details.

## Tools
- `serve.py <folder> <port>`: static server on the Wi-Fi, video seeking (Range), no-cache, prints the phone link. Use it in place of `python -m http.server`, whose videos can't seek.
- `phonecheck.py <port> [path]`: finds today's PC Wi-Fi IP, tests the Wi-Fi address and prints both links (PASS) or why the phone link fails (FAIL).
- `copybar.js`: every picker / choice page gets the "copy this into the chat" line in a sticky bar at the TOP with a big Copy button (at the bottom it was hard to copy on a phone). Inline it (pages live on many ports, never link by path); it mirrors an element `#out` or takes `CopyBar.set(text)`. On `http://<Wi-Fi IP>` the clipboard API is blocked (not a secure context), so it falls back to a selected textarea + `execCommand('copy')`; if even that fails the button says "Select + copy" and selects the text.
  - Picker buttons: a second tap un-picks; any "Fix all" / "select all" has a **Clear all** next to it; every item gets its own note input whose text goes into the copy line. The bar mirrors `#out` through a MutationObserver, so it updates a tick after the click (tests must wait).
- Firewall: the ports you serve on (e.g. 3000–5999 and 8000–8999) must be open to the home (Private) Wi-Fi; open them once in your OS firewall settings.

## The IP changes
The PC's Wi-Fi IP can change from day to day: check it every time with phonecheck; an old IP is always suspect.

## When the phone can't connect
Servers Claude starts can be sandboxed to this PC only (`127.0.0.1`).
- Check with `netstat -ano | findstr LISTENING` (Windows) or `lsof -iTCP -sTCP:LISTEN` (Mac): phone access needs `0.0.0.0:<port>`.
- Give the user a double-click launcher (a `.bat` / `.command` that runs `serve.py`) so the server starts outside Claude, then run phonecheck again.
- Port already taken: `serve.py` on a port another chat serves fails silently and the link shows THAT chat's page. Pick a free port first (`Get-NetTCPConnection -LocalPort <p> -State Listen` on Windows), then phonecheck. On Windows run phonecheck from PowerShell: Git Bash rewrites `/picker/` into a Windows path.

## Pages work on phone screens
- No sideways overflow at 375 px.
- Grids use `minmax(min(Npx,100%),1fr)`.
- Fixed-size demos scale down to fit.
- Videos have `playsinline`, and `play()` is called inside the tap (iOS Safari blocks it otherwise).
- If the phone shows an old version, tell the user to reload the page.
