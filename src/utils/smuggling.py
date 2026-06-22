"""
HTML Smuggling — generate HTML pages for file download delivery.
"""

import base64
import hashlib
import json
from dataclasses import dataclass, field
from html import escape

SAFE_SMUGGLE_EXTENSIONS: tuple[str, ...] = ("txt", "bin", "dat", "zip", "pdf")
SAFE_SMUGGLE_PRESETS: tuple[str, ...] = ("direct", "card_manual", "card_auto")


@dataclass(frozen=True)
class SmugglingRenderOptions:
    """Closed renderer options for generated SMUGGLE artifacts."""

    crypto_js_src: str = "/static/crypto-js.min.js"


@dataclass(frozen=True)
class SmugglingRenderContext:
    """Internal renderer context after payload preparation."""

    filename: str
    base64_data: str
    encrypted: bool
    password_captcha: str | None = None
    options: SmugglingRenderOptions = field(default_factory=SmugglingRenderOptions)


@dataclass(frozen=True)
class SafeSmuggleBuilderConfig:
    """Closed safe-builder options for lab-only SMUGGLE artifacts."""

    download_name: str | None = None
    download_ext: str | None = None
    preset: str = "direct"
    title: str | None = None
    message: str | None = None
    cta_label: str | None = None
    delay_ms: int = 0
    show_notice: bool = True


def xor_encrypt(data: bytes, password: str) -> bytes:
    """
    XOR encryption using a SHA256-derived key.

    NOTE: This implementation intentionally differs from security/crypto.py!
    - security/crypto.py: XOR with raw password (for advanced upload payloads)
    - utils/smuggling.py: XOR with SHA256(password) (for HTML Smuggling / browser)

    The browser-side JavaScript (CryptoJS.SHA256) uses a SHA256-derived key,
    so the server-side HTML Smuggling must do the same.
    Do NOT merge these implementations — they serve different protocols.
    """
    key = hashlib.sha256(password.encode("utf-8")).digest()
    key_len = len(key)

    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % key_len])

    return bytes(result)


def generate_smuggling_html(
    file_data: bytes,
    filename: str,
    password: str | None = None,
    password_captcha: str | None = None,
    crypto_js_src: str = "/static/crypto-js.min.js",
    builder: SafeSmuggleBuilderConfig | None = None,
) -> str:
    """
    Generate an HTML page for HTML Smuggling file delivery.

    Args:
        file_data: File contents.
        filename: Filename for the download.
        password: Password for XOR encryption (None = no encryption).
        password_captcha: Base64 data URI of a CAPTCHA image with the password (optional).
        crypto_js_src: Path to crypto-js (only needed with encryption).

    Returns:
        HTML page string.
    """
    resolved_filename = (
        resolve_safe_smuggle_download_filename(
            source_filename=filename,
            download_name=builder.download_name,
            download_ext=builder.download_ext,
        )
        if builder is not None
        else filename
    )

    if password:
        # Encrypt and encode to base64
        encrypted = xor_encrypt(file_data, password)
        context = SmugglingRenderContext(
            filename=resolved_filename,
            base64_data=base64.b64encode(encrypted).decode("utf-8"),
            encrypted=True,
            password_captcha=password_captcha,
            options=SmugglingRenderOptions(crypto_js_src=crypto_js_src),
        )
    else:
        # Plain base64
        context = SmugglingRenderContext(
            filename=resolved_filename,
            base64_data=base64.b64encode(file_data).decode("utf-8"),
            encrypted=False,
        )

    if builder is not None:
        return _render_safe_smuggling_html(context, builder)
    return _render_smuggling_html(context)


def resolve_safe_smuggle_download_filename(
    source_filename: str,
    download_name: str | None,
    download_ext: str | None,
) -> str:
    """Resolve the download-facing filename for a safe builder request."""
    name_parts = source_filename.rsplit(".", 1)
    source_stem = name_parts[0] if len(name_parts) == 2 and name_parts[0] else source_filename
    source_ext = name_parts[1] if len(name_parts) == 2 else ""

    stem = _normalize_safe_smuggle_stem((download_name or source_stem).strip())
    requested_ext = (download_ext or "").strip().lstrip(".").lower()
    normalized_source_ext = source_ext.strip().lstrip(".").lower()
    if requested_ext in SAFE_SMUGGLE_EXTENSIONS:
        ext = requested_ext
    elif normalized_source_ext in SAFE_SMUGGLE_EXTENSIONS:
        ext = normalized_source_ext
    else:
        ext = "bin"
    return f"{stem}.{ext}" if ext else stem


def _normalize_safe_smuggle_stem(stem: str) -> str:
    """Collapse a download stem into a local filename token."""
    normalized_chars: list[str] = []
    for char in stem:
        if char.isalnum() or char in {"-", "_", " "}:
            normalized_chars.append(char)
            continue
        if char in {".", "/", "\\", "\r", "\n", "\t"} or ord(char) < 32 or ord(char) == 127:
            normalized_chars.append("-")
            continue
        normalized_chars.append("-")

    normalized = "".join(normalized_chars)
    normalized = " ".join(normalized.split()).replace(" ", "-")
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    normalized = normalized.strip("._- ")
    return normalized or "download"


def _safe_script_json(value: str) -> str:
    """Serialize a string for safe use inside an inline <script> block."""
    return json.dumps(value).replace("</", "<\\/")


def _render_smuggling_html(context: SmugglingRenderContext) -> str:
    """Render the prepared SMUGGLE artifact HTML."""
    if context.encrypted:
        return _create_html_with_password(
            context.base64_data,
            context.filename,
            context.options.crypto_js_src,
            context.password_captcha,
        )
    return _create_html_no_password(context.base64_data, context.filename)


def _render_safe_smuggling_html(
    context: SmugglingRenderContext,
    builder: SafeSmuggleBuilderConfig,
) -> str:
    """Render a safe, closed lab-only SMUGGLE artifact page."""
    if context.encrypted:
        return _create_safe_html_with_password(
            encrypted_data=context.base64_data,
            filename=context.filename,
            crypto_js_src=context.options.crypto_js_src,
            builder=builder,
            captcha_img=context.password_captcha,
        )
    return _create_safe_html_no_password(
        base64_data=context.base64_data,
        filename=context.filename,
        builder=builder,
    )


def _resolve_safe_builder_copy(
    builder: SafeSmuggleBuilderConfig,
    *,
    encrypted: bool = False,
) -> tuple[str, str, str, str]:
    """Return escaped copy for the safe builder chrome."""
    default_title = "Protected test artifact" if encrypted else "Test artifact ready"
    default_message = (
        "Enter the verification password to download the internal lab test artifact."
        if encrypted
        else "Internal lab test artifact"
    )
    title = escape((builder.title or "").strip() or default_title, quote=True)
    message = escape((builder.message or "").strip() or default_message, quote=True)
    cta_label = escape((builder.cta_label or "").strip() or "Download test artifact", quote=True)
    notice = (
        '<p class="notice">Test artifact notice: internal lab-only page.</p>'
        if builder.show_notice
        else ""
    )
    return title, message, cta_label, notice


def _create_safe_html_no_password(
    base64_data: str,
    filename: str,
    builder: SafeSmuggleBuilderConfig,
) -> str:
    """Render one of the closed safe lab-only non-encrypted builder presets."""
    safe_filename = escape(filename, quote=True)
    title, message, cta_label, notice = _resolve_safe_builder_copy(builder)
    preset = builder.preset if builder.preset in SAFE_SMUGGLE_PRESETS else "direct"
    delay_ms = max(int(builder.delay_ms), 0)
    countdown_markup = ""
    button_markup = ""
    auto_start_script = ""
    countdown_script = ""
    initial_status = "Preparing download..."

    if preset == "card_manual":
        button_markup = (
            f'<button type="button" class="action" id="downloadBtn" '
            f'onclick="startDownload()">{cta_label}</button>'
        )
        initial_status = "Ready to download."
    elif preset == "card_auto":
        button_markup = (
            f'<button type="button" class="action" id="downloadBtn" '
            f'onclick="startDownload()">{cta_label}</button>'
        )
        countdown_markup = (
            '<p class="countdown">Auto-download in '
            '<span id="smuggleCountdown"></span>s.</p>'
        )
        initial_status = "Auto-download scheduled."
        countdown_script = f"""
var countdownTarget=document.getElementById("smuggleCountdown");
var countdownStart=Date.now();
var countdownDuration={delay_ms};
function updateCountdown(){{
if(!countdownTarget)return;
var remaining=Math.max(0,countdownDuration-(Date.now()-countdownStart));
countdownTarget.textContent=(remaining/1000).toFixed(1);
if(remaining>0)window.requestAnimationFrame(updateCountdown);
}}
updateCountdown();
setTimeout(startDownload, {delay_ms});
"""
    else:
        auto_start_script = "setTimeout(startDownload, 500);"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Test Artifact</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#0f172a;color:#e2e8f0}}
.shell{{max-width:640px;margin:40px auto;padding:24px}}
.card{{background:#111827;border:1px solid #334155;border-radius:16px;padding:24px;box-shadow:0 18px 45px rgba(15,23,42,.35)}}
.badge{{display:inline-block;margin:0 0 12px;padding:6px 10px;border-radius:999px;background:#1d4ed8;color:#eff6ff;font-size:.78rem;font-weight:bold;letter-spacing:.04em;text-transform:uppercase}}
.notice{{margin:0 0 16px;padding:12px 14px;border-radius:12px;background:#1e293b;color:#bfdbfe}}
h2{{margin:0 0 8px;color:#f8fafc}}
.message{{margin:0 0 16px;color:#cbd5e1;line-height:1.6}}
.file{{margin:0 0 16px;color:#94a3b8}}
.file strong{{color:#f8fafc}}
.countdown,.status{{margin:14px 0 0;color:#93c5fd}}
.action{{margin-top:18px;padding:12px 18px;border:0;border-radius:12px;background:#38bdf8;color:#082f49;font-weight:bold;cursor:pointer}}
</style>
</head>
<body>
<div class="shell">
  <div class="card">
    <p class="badge">Test artifact</p>
    {notice}
    <h2>{title}</h2>
    <p class="message">{message}</p>
    <p class="file">Download name: <strong>{safe_filename}</strong></p>
    {countdown_markup}
    {button_markup}
    <p class="status" id="smuggleStatus">{initial_status}</p>
  </div>
</div>
<script>
var fn={_safe_script_json(filename)};
var data={_safe_script_json(base64_data)};
function startDownload(){{
try{{
var status=document.getElementById("smuggleStatus");
if(status)status.textContent="Processing...";
var raw=atob(data);
var bytes=new Uint8Array(raw.length);
for(var i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
var blob=new Blob([bytes],{{type:"application/octet-stream"}});
var url=window.URL.createObjectURL(blob);
var el=document.createElement("a");
el.href=url;
el.download=fn;
document.body.appendChild(el);
el.click();
document.body.removeChild(el);
window.URL.revokeObjectURL(url);
if(status)status.textContent="Downloaded: "+fn;
}}catch(e){{
var status=document.getElementById("smuggleStatus");
if(status)status.textContent="Error: "+e.message;
}}
}}
{countdown_script or auto_start_script}
</script>
</body>
</html>"""


def _create_safe_html_with_password(
    encrypted_data: str,
    filename: str,
    crypto_js_src: str,
    builder: SafeSmuggleBuilderConfig,
    captcha_img: str | None = None,
) -> str:
    """Render the safe builder shell around the existing password flow."""
    title, message, cta_label, notice = _resolve_safe_builder_copy(builder, encrypted=True)
    safe_crypto_js_src = escape(crypto_js_src, quote=True)
    safe_filename = escape(filename, quote=True)
    captcha_block = ""
    if captcha_img:
        captcha_block = f"""
<div class="captcha-box">
<p class="captcha-label">Password:</p>
<img src="{captcha_img}" alt="Password" class="captcha-img" draggable="false" oncontextmenu="return false;">
</div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Protected Test Artifact</title>
<style>
body{{font-family:Arial,sans-serif;max-width:460px;margin:50px auto;padding:20px;background:#0f172a;color:#e2e8f0}}
.card{{background:#111827;border:1px solid #334155;border-radius:16px;padding:24px;box-shadow:0 18px 45px rgba(15,23,42,.35)}}
.badge{{display:inline-block;margin:0 0 12px;padding:6px 10px;border-radius:999px;background:#1d4ed8;color:#eff6ff;font-size:.78rem;font-weight:bold;letter-spacing:.04em;text-transform:uppercase}}
.notice{{margin:0 0 16px;padding:12px 14px;border-radius:12px;background:#1e293b;color:#bfdbfe}}
h3{{margin:0 0 8px;color:#f8fafc}}
.message{{margin:0 0 16px;color:#cbd5e1;line-height:1.6}}
.file{{margin:0 0 16px;color:#94a3b8}}
.file strong{{color:#f8fafc}}
input{{width:100%;padding:12px;margin:10px 0;border:1px solid #475569;border-radius:12px;box-sizing:border-box;background:#020617;color:#fff;font-size:1rem}}
input:focus{{outline:none;border-color:#38bdf8}}
button{{width:100%;padding:12px;background:#38bdf8;color:#082f49;border:none;border-radius:12px;cursor:pointer;font-size:1rem;font-weight:bold}}
.msg{{color:#888;margin:15px 0;font-size:14px;text-align:center}}
.err{{color:#f87171}}
.ok{{color:#4ade80}}
.captcha-box{{background:#0f172a;border:1px solid #334155;border-radius:12px;padding:15px;margin:15px 0;text-align:center}}
.captcha-label{{color:#94a3b8;font-size:0.85rem;margin:0 0 10px 0}}
.captcha-img{{max-width:100%;height:auto;border-radius:4px;user-select:none;-webkit-user-select:none;-moz-user-select:none;-ms-user-select:none}}
</style>
</head>
<body>
<div class="card">
<p class="badge">Test artifact</p>
{notice}
<h3>{title}</h3>
<p class="message">{message}</p>
<p class="file">Download name: <strong>{safe_filename}</strong></p>
{captcha_block}
<input type="password" id="p" placeholder="Password" autofocus>
<button onclick="d()">{cta_label}</button>
<div class="msg" id="m"></div>
</div>
<script src="{safe_crypto_js_src}"></script>
<script>
var fn={_safe_script_json(filename)};
var encData={_safe_script_json(encrypted_data)};
function d(){{
var pw=document.getElementById("p").value;
if(!pw){{msg("Enter password","err");return}}
msg("Decrypting...","");
try{{
var hash=CryptoJS.SHA256(pw);
var key=[];
for(var i=0;i<hash.words.length;i++){{
var w=hash.words[i]>>>0;
key.push((w>>>24)&0xff);
key.push((w>>>16)&0xff);
key.push((w>>>8)&0xff);
key.push(w&0xff);
}}
var raw=atob(encData);
var dec=new Uint8Array(raw.length);
for(var i=0;i<raw.length;i++)dec[i]=raw.charCodeAt(i)^key[i%key.length];
var blob=new Blob([dec],{{type:"application/octet-stream"}});
var url=window.URL.createObjectURL(blob);
var el=document.createElement("a");
el.href=url;
el.download=fn;
document.body.appendChild(el);
el.click();
document.body.removeChild(el);
window.URL.revokeObjectURL(url);
msg("Downloaded: "+fn,"ok");
}}catch(e){{
msg("Error: "+e.message,"err");
}}
}}
function msg(t,c){{var m=document.getElementById("m");m.textContent=t;m.className="msg "+c}}
document.getElementById("p").addEventListener("keypress",function(e){{if(e.key==="Enter")d()}});
</script>
</body>
</html>"""


def _create_html_no_password(base64_data: str, filename: str) -> str:
    """HTML without password — automatic download."""
    safe_fn = json.dumps(filename)[1:-1]
    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Download</title>
<style>
body{{font-family:Arial,sans-serif;max-width:600px;margin:50px auto;padding:20px;text-align:center;background:#1a1a2e;color:#eee}}
h2{{color:#00d4ff}}
.status{{color:#888;margin:20px 0}}
</style>
</head>
<body>
<h2>Downloading...</h2>
<div class="status" id="s">Preparing file...</div>
<script>
var fn="{safe_fn}";
var data="{base64_data}";
function d(){{
try{{
document.getElementById("s").textContent="Processing...";
var b=atob(data);
var a=new Uint8Array(b.length);
for(var i=0;i<b.length;i++)a[i]=b.charCodeAt(i);
var blob=new Blob([a],{{type:"application/octet-stream"}});
var url=window.URL.createObjectURL(blob);
var el=document.createElement("a");
el.href=url;
el.download=fn;
document.body.appendChild(el);
el.click();
document.body.removeChild(el);
window.URL.revokeObjectURL(url);
document.getElementById("s").textContent="Done! File: "+fn;
}}catch(e){{document.getElementById("s").textContent="Error: "+e.message}}
}}
setTimeout(d,500);
</script>
</body>
</html>'''


def _create_html_with_password(
    encrypted_data: str,
    filename: str,
    crypto_js_src: str,
    captcha_img: str | None = None,
) -> str:
    """HTML with password — password input form."""
    safe_fn = json.dumps(filename)[1:-1]
    safe_crypto_js_src = escape(crypto_js_src, quote=True)
    # CAPTCHA block (if provided)
    captcha_block = ""
    if captcha_img:
        captcha_block = f'''
<div class="captcha-box">
<p class="captcha-label">Password:</p>
<img src="{captcha_img}" alt="Password" class="captcha-img" draggable="false" oncontextmenu="return false;">
</div>'''

    # Inline SHA256 implementation (no external dependencies)
    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Protected Download</title>
<style>
body{{font-family:Arial,sans-serif;max-width:400px;margin:50px auto;padding:20px;background:#1a1a2e;color:#eee}}
h3{{color:#00d4ff;text-align:center}}
input{{width:100%;padding:12px;margin:10px 0;border:1px solid #30363d;border-radius:8px;box-sizing:border-box;background:#0d1117;color:#fff;font-size:1rem}}
input:focus{{outline:none;border-color:#00d4ff}}
button{{width:100%;padding:12px;background:#00d4ff;color:#000;border:none;border-radius:8px;cursor:pointer;font-size:1rem;font-weight:bold}}
button:hover{{background:#00b8e6}}
.msg{{color:#888;margin:15px 0;font-size:14px;text-align:center}}
.err{{color:#f87171}}
.ok{{color:#4ade80}}
.info{{color:#666;font-size:0.85rem;text-align:center;margin-top:20px}}
.captcha-box{{background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:15px;margin:15px 0;text-align:center}}
.captcha-label{{color:#888;font-size:0.85rem;margin:0 0 10px 0}}
.captcha-img{{max-width:100%;height:auto;border-radius:4px;user-select:none;-webkit-user-select:none;-moz-user-select:none;-ms-user-select:none}}
</style>
</head>
<body>
<h3>Protected File</h3>{captcha_block}
<p class="info">Enter password to download</p>
<input type="password" id="p" placeholder="Password" autofocus>
<button onclick="d()">Download</button>
<div class="msg" id="m"></div>
<script src="{safe_crypto_js_src}"></script>
<script>
var fn="{safe_fn}";
var encData="{encrypted_data}";
function d(){{
var pw=document.getElementById("p").value;
if(!pw){{msg("Enter password","err");return}}
msg("Decrypting...","");
try{{
var hash=CryptoJS.SHA256(pw);
var key=[];
for(var i=0;i<hash.words.length;i++){{
var w=hash.words[i]>>>0;
key.push((w>>>24)&0xff);
key.push((w>>>16)&0xff);
key.push((w>>>8)&0xff);
key.push(w&0xff);
}}
var raw=atob(encData);
var dec=new Uint8Array(raw.length);
for(var i=0;i<raw.length;i++)dec[i]=raw.charCodeAt(i)^key[i%key.length];
var blob=new Blob([dec],{{type:"application/octet-stream"}});
var url=window.URL.createObjectURL(blob);
var el=document.createElement("a");
el.href=url;
el.download=fn;
document.body.appendChild(el);
el.click();
document.body.removeChild(el);
window.URL.revokeObjectURL(url);
msg("Downloaded: "+fn,"ok");
}}catch(e){{
msg("Error: "+e.message,"err");
}}
}}
function msg(t,c){{var m=document.getElementById("m");m.textContent=t;m.className="msg "+c}}
document.getElementById("p").addEventListener("keypress",function(e){{if(e.key==="Enter")d()}});
</script>
</body>
</html>'''
