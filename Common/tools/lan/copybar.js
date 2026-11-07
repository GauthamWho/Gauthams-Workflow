/* copybar.js: the user's rule (2026-11-07): on every picker / choice page, the "copy this into the chat" line sits
   at the TOP (sticky, always visible on the iPhone) with a big Copy button. Inline this whole file in a <script> at the
   end of <body> (pages are served from many folders/ports, so never link it by path).
   Use: CopyBar.set("Looks: skin C, ...")  -- or keep an element with id="out": the bar mirrors its text.
   Copy works on http://<PC Wi-Fi IP> too (no secure context there, so it falls back to a selected textarea + execCommand). */
(function () {
  var css = "#cb-bar{position:sticky;top:0;z-index:9999;display:flex;gap:8px;align-items:center;background:#2a2420;color:#fff;" +
    "padding:10px 12px;margin:-16px -16px 14px;font:15px system-ui;box-shadow:0 2px 10px rgba(0,0,0,.25)}" +
    "#cb-text{flex:1;min-width:0;font-family:ui-monospace,Menlo,monospace;font-size:13px;line-height:1.3;max-height:3.9em;overflow:auto;word-break:break-word}" +
    "#cb-btn{flex:none;font:700 16px system-ui;padding:12px 18px;border:0;border-radius:10px;background:#f2c14e;color:#2a2420;min-width:96px}" +
    "#cb-btn.ok{background:#7bd389}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  var bar = document.createElement("div"); bar.id = "cb-bar";
  bar.innerHTML = '<div id="cb-text">Tap your picks below</div><button id="cb-btn" type="button">Copy</button>';
  document.body.insertBefore(bar, document.body.firstChild);
  var txt = bar.querySelector("#cb-text"), btn = bar.querySelector("#cb-btn"), value = "";
  function set(v) { value = v || ""; txt.textContent = value || "Tap your picks below"; }
  function fallback(v) {
    var ta = document.createElement("textarea"); ta.value = v; ta.setAttribute("readonly", "");
    ta.style.cssText = "position:fixed;top:0;left:0;opacity:0;font-size:16px"; document.body.appendChild(ta);
    ta.focus(); ta.select(); ta.setSelectionRange(0, v.length);
    var ok = false; try { ok = document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta); return ok;
  }
  function done(ok) {
    btn.textContent = ok ? "Copied ✓" : "Select + copy"; btn.classList.toggle("ok", ok);
    if (!ok) { var r = document.createRange(); r.selectNodeContents(txt); var s = getSelection(); s.removeAllRanges(); s.addRange(r); }
    setTimeout(function () { btn.textContent = "Copy"; btn.classList.remove("ok"); }, 1800);
  }
  btn.addEventListener("click", function () {
    if (!value) return done(false);
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(value).then(function () { done(true); }, function () { done(fallback(value)); });
    else done(fallback(value));
  });
  var out = document.getElementById("out");
  if (out) { var sync = function () { var t = out.textContent.trim(); set(t === "-" ? "" : t); }; new MutationObserver(sync).observe(out, { childList: true, characterData: true, subtree: true }); sync(); }
  window.CopyBar = { set: set };
})();
