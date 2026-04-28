# Experimental HTTP Server

![Python 3.10-3.13](https://img.shields.io/badge/Python-3.10--3.13-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)
[![CI](https://github.com/gkumurzhi/ExperimentalServer/actions/workflows/ci.yml/badge.svg)](https://github.com/gkumurzhi/ExperimentalServer/actions/workflows/ci.yml)
[![Security](https://github.com/gkumurzhi/ExperimentalServer/actions/workflows/security.yml/badge.svg)](https://github.com/gkumurzhi/ExperimentalServer/actions/workflows/security.yml)
![Type checked](https://img.shields.io/badge/mypy-strict-blue.svg)
![Lint](https://img.shields.io/badge/ruff-passing-blue.svg)

HTTP-сервер с поддержкой произвольных HTTP-методов, написанный на чистом Python без внешних зависимостей.

📄 **Документация:** [Threat Model](docs/threat-model.md) · [ADR](docs/ADR/) · [Security Policy](SECURITY.md) · [Contributing](CONTRIBUTING.md) · [Examples](examples/) · [Docker](Dockerfile)

## Содержание

- [Возможности](#возможности)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Структура проекта](#структура-проекта)
- [Запуск](#запуск)
- [HTTP-методы](#http-методы)
- [Веб-интерфейс](#веб-интерфейс)
- [Продвинутая загрузка](#продвинутая-загрузка)
- [HTTPS/TLS](#httpstls)
- [Basic Auth](#basic-auth)
- [Область доступа uploads/](#область-доступа-uploads)
- [HTML Smuggling](#html-smuggling)
- [Утилита расшифровки](#утилита-расшифровки)
- [Использование как библиотеки](#использование-как-библиотеки)
- [API примеры](#api-примеры)
- [Безопасность](#безопасность)
- [Технические детали](#технические-детали)
- [Разработка](#разработка)

## Возможности

- Кастомные HTTP-методы: `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`, `FETCH`, `INFO`, `PING`, `NONE`, `NOTE`, `SMUGGLE`, `OPTIONS`
- Загрузка файлов через методы `NONE`, `POST`, `PUT`, `PATCH`
- Скачивание файлов через метод `FETCH` с заголовками для загрузки
- Получение метаданных файлов/директорий через `INFO` (JSON)
- **Secure Notepad** — метод `NOTE` с end-to-end шифрованием AES-256-GCM и ECDH P-256 (требует `exphttp[crypto]`)
- **WebSocket** — реал-тайм синхронизация блокнота (RFC 6455) по `/notes/ws`
- **HTTPS/TLS** — самоподписные сертификаты на лету или свои
- **Basic Auth** — HTTP аутентификация с генерацией паролей
- **Загрузка (продвинутая)** — загрузка через JSON body, заголовки или URL-параметры
- **Доступ только к `uploads/`** — файловые операции по умолчанию ограничены рабочей папкой загрузок
- **Многопоточность** — ThreadPoolExecutor для параллельной обработки
- Ограничение размера загрузки (по умолчанию 100 MB)
- Веб-интерфейс с drag & drop загрузкой
- Модульная архитектура (mixin-паттерн)
- Поддержка кириллических имён файлов

## Требования

- Python 3.10 — 3.13 (эта матрица проверяется в CI; используются type hints с `|` синтаксисом)
- Стандартная библиотека (без внешних зависимостей для runtime)
- OpenSSL (опционально, для генерации TLS сертификатов)
- Typed package (PEP 561) — поддержка статической типизации

## Быстрый старт

```bash
pip install -e .
exphttp --open
```

Сервер запустится на `http://127.0.0.1:8080` и откроет браузер. Все пользовательские файлы читаются и записываются через `<root>/uploads/`; встроенный `index.html` и `/static/...` отдаются только для загрузки веб-интерфейса.

Полезные комбинации:
```bash
exphttp --tls --auth random    # HTTPS + авто-пароль
exphttp -d ./data -m 500       # Рабочая папка ./data/uploads, лимит 500 MB
exphttp -H 0.0.0.0 -p 443     # Публичный доступ
```

## Структура проекта

```
ExperimentalHTTPServer/
├── pyproject.toml         # Конфигурация проекта
├── README.md
├── CLAUDE.md              # Инструкции для AI
│
├── src/                   # Исходный код
│   ├── __init__.py
│   ├── __main__.py        # python -m src
│   ├── cli.py             # CLI интерфейс
│   ├── server.py          # socket lifecycle, keep-alive, WebSocket helpers
│   ├── config.py          # Константы и конфигурация
│   ├── metrics.py         # thread-safe метрики сервера
│   ├── notepad_service.py # NOTE-домен, общий для HTTP и WebSocket
│   ├── request_pipeline.py# auth/dispatch/send orchestration
│   ├── websocket.py       # WebSocket RFC 6455
│   ├── py.typed           # PEP 561 marker
│   │
│   ├── http/              # HTTP модули
│   │   ├── request.py     # HTTPRequest
│   │   ├── response.py    # HTTPResponse
│   │   ├── io.py          # приём запроса + лимиты/таймауты
│   │   └── utils.py       # path helpers, sanitize, etc
│   │
│   ├── handlers/          # Обработчики методов
│   │   ├── base.py        # BaseHandler
│   │   ├── files.py       # GET, HEAD, POST, PUT, PATCH, DELETE, FETCH, NONE
│   │   ├── info.py        # INFO, PING
│   │   ├── notepad.py     # NOTE HTTP handlers
│   │   ├── advanced_upload.py # Advanced upload
│   │   ├── registry.py    # HandlerRegistry
│   │   └── smuggle.py     # HTML Smuggling
│   │
│   ├── security/          # Безопасность
│   │   ├── auth.py        # Basic Auth + rate limiting
│   │   ├── crypto.py      # XOR/HMAC/AES-256-GCM
│   │   ├── keys.py        # ECDH P-256 key exchange
│   │   ├── tls.py         # генерация/получение сертификатов
│   │   └── tls_manager.py # SSL context lifecycle + temp cert cleanup
│   │
│   ├── utils/             # Утилиты
│   │   ├── captcha.py
│   │   └── smuggling.py
│   │
│   └── data/              # Встроенные ресурсы
│       ├── index.html     # Веб-интерфейс
│       └── static/        # JS, CSS
│
├── tests/                 # Тесты
│   ├── conftest.py
│   ├── test_http/
│   ├── test_security/
│   └── test_handlers/
│
├── tools/                 # CLI утилиты
│   ├── browser_smoke.py
│   ├── decrypt.py
│   └── sync_docs.py
│
└── uploads/               # Загруженные файлы
```

## Запуск

```bash
python -m src [опции]
# или
exphttp [опции]
```

### Параметры командной строки

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `-H, --host HOST` | Хост для привязки | `127.0.0.1` |
| `-p, --port PORT` | Порт для прослушивания | `8080` |
| `-d, --dir DIR` | Корневая директория | `.` |
| `-m, --max-size MB` | Макс. размер загрузки в MB | `100` |
| `-w, --workers N` | Количество worker потоков | `10` |
| `-q, --quiet` | Тихий режим (минимум логов) | выключен |
| `--debug` | Debug режим (подробное логирование) | выключен |
| `--open` | Открыть в браузере после запуска | выключен |
| `--json-log` | Структурированный JSON формат логов | выключен |
| `--cors-origin ORIGIN` | Разрешить CORS для указанного origin | выключен |
| `--advanced-upload` | Включить продвинутую загрузку через неизвестные HTTP-методы | выключен |
| `--tls` | Включить HTTPS (самоподписный сертификат) | выключен |
| `--cert FILE` | Путь к сертификату (PEM) | - |
| `--key FILE` | Путь к приватному ключу (PEM) | - |
| `--letsencrypt` | Получить сертификат Let's Encrypt | выключен |
| `--domain DOMAIN` | Домен для Let's Encrypt | - |
| `--email EMAIL` | Email для Let's Encrypt уведомлений | - |
| `--auth USER:PASS` | Включить Basic Auth | выключен |
| `--auth random` | Сгенерировать случайные credentials в интерактивном терминале | - |
| `--help` | Показать справку | - |

### Примеры запуска

```bash
# Стандартный запуск (localhost:8080)
exphttp

# HTTPS с самоподписным сертификатом
exphttp --tls

# HTTPS с Basic Auth (случайные credentials)
exphttp --tls --auth random

# HTTPS с своими credentials
exphttp --tls --auth admin:secretpassword

# HTTPS с готовыми сертификатами
exphttp --tls --cert cert.pem --key key.pem

# Публичный доступ на порту 443
exphttp -H 0.0.0.0 -p 443 --tls --auth admin:pass

# Комбинированный режим
exphttp -H 0.0.0.0 -p 8080 -d ./data --tls --auth random -m 200
```

## HTTP-методы

| Метод | Описание | Область доступа |
|-------|----------|---------|
| `GET` | Получение встроенного UI, статических ресурсов и файлов загрузок | UI + `uploads/` |
| `HEAD` | Заголовки GET без тела ответа | UI + `uploads/` |
| `POST` | Загрузка файлов на сервер | `uploads/` |
| `PUT` | Загрузка файлов на сервер | `uploads/` |
| `PATCH` | Загрузка файлов на сервер | `uploads/` |
| `DELETE` | Удаление файла из uploads/ | Только uploads/ |
| `OPTIONS` | CORS preflight | n/a |
| `FETCH` | Скачивание файлов с Content-Disposition | Только uploads/ |
| `INFO` | Метаданные файла/директории (JSON) | Только uploads/ |
| `PING` | Проверка доступности сервера | n/a |
| `NONE` | Загрузка файлов на сервер | `uploads/` |
| `NOTE` | Защищённый блокнот (ECDH + AES-256-GCM, требует `exphttp[crypto]`) | Только notes/ |
| `SMUGGLE` | HTML Smuggling — генерация страницы со встроенным файлом | Только uploads/ |
| Любой нестандартный метод с payload | Загрузка (продвинутая) через `d`/`data`, `X-D` или `?d=` | `uploads/` |

### Заголовки ответов

| Заголовок | Методы | Описание |
|-----------|--------|----------|
| `X-File-Name` | FETCH, NONE | Имя файла |
| `X-File-Size` | FETCH, NONE | Размер в байтах |
| `X-File-Path` | NONE | Путь к загруженному файлу |
| `X-File-Modified` | FETCH | Дата модификации (ISO) |
| `X-Upload-Status` | NONE | success / error / no-data |
| `X-Fetch-Status` | FETCH | success / file-not-found |
| `X-Ping-Response` | PING | pong |
| `X-Request-Id` | Все HTTP-ответы | 8-символьный hex ID для корреляции логов |
| `Content-Security-Policy` | GET (HTML) | CSP заголовок для HTML ответов |

## Веб-интерфейс

Откройте `http://localhost:8080` в браузере. Вкладки:

1. **Запросы** — отправка `GET`, `FETCH`, `INFO`, `PING` по произвольному пути
2. **Загрузка файлов** — drag & drop интерфейс с переключателем метода `POST` / `NONE` / `PUT` / `PATCH`
3. **Загрузка (продвинутая)** — загрузка через JSON body, заголовки или URL-параметры, с опциональным XOR-шифрованием; требует запуска с `--advanced-upload`
4. **Скачивание** — обзор `uploads/`, переход по директориям, `INFO`, `FETCH`, `SMUGGLE`, удаление файлов и быстрая очистка `uploads/`
5. **Secure Notepad** — ECDH/AES-GCM блокнот с автошифрованием и переключением транспорта `HTTP` / `WebSocket`

## Продвинутая загрузка

Продвинутый сценарий загрузки выключен по умолчанию. Запустите сервер с
`--advanced-upload`, чтобы неизвестные HTTP-методы с payload принимались как
загрузка в `uploads/`.

### Особенности

- **Явное включение** — неизвестные HTTP-методы обрабатываются как продвинутая загрузка только при `--advanced-upload`
- **Несколько транспортов** — payload можно передать через JSON body, HTTP headers или URL query
- **Base64-кодирование** — данные передаются как `d` / `data`
- **XOR** — при наличии ключа payload можно обфусцировать перед передачей
- **Имя файла опционально** — если `n` / `name` не передано, сервер сохранит `<sha256[:12]>.bin`

### Формат запроса

```json
{
  "d": "base64_encoded_data",
  "n": "filename.txt",
  "e": "xor",
  "k": "encryption_key",
  "h": "hmac_sha256_hex"
}
```

| Поле | Описание | Обязательное |
|------|----------|--------------|
| `d` / `data` | Данные файла в Base64 | да |
| `n` / `name` | Имя файла | нет (генерируется SHA256[:12].bin) |
| `e` | Тип шифрования (`xor`) | нет |
| `k` | Ключ для расшифровки на сервере | нет |
| `h` / `hmac` | HMAC-SHA256 для проверки целостности | нет |

### HMAC проверка целостности

Для защиты от повреждения данных можно передать HMAC:

```python
from src import xor_encrypt_with_hmac
import base64

data = b"Secret content"
password = "mykey"

encrypted, hmac_tag = xor_encrypt_with_hmac(data, password)
payload = {
    "d": base64.b64encode(encrypted).decode(),
    "n": "secret.txt",
    "e": "xor",
    "k": password,
    "h": hmac_tag  # HMAC-SHA256
}
```

Сервер проверит HMAC перед расшифровкой и вернёт ошибку если данные повреждены.

### Пример продвинутой загрузки

```bash
# 1. Зашифровать файл локально
python tools/decrypt.py secret.txt mykey -e -o secret.enc

# 2. Закодировать в Base64
base64 secret.enc > secret.b64

# 3. Запустить сервер с --advanced-upload и отправить payload нестандартным методом
curl -X CHECKDATA -H "Content-Type: application/json" \
  -d '{"d":"'$(cat secret.b64)'","n":"secret.txt","e":"xor","k":"mykey"}' \
  http://localhost:8080/
```

### Ответ

```json
{
  "ok": true,
  "id": "a1b2c3d4e5f67890",
  "sz": 1234
}
```

## HTTPS/TLS

Сервер поддерживает HTTPS с автоматической генерацией самоподписных сертификатов.

### Автоматическая генерация

```bash
# Генерирует временный сертификат (требует OpenSSL)
exphttp --tls
```

Сертификат создаётся с:
- RSA 2048 bit ключ
- Срок действия: 365 дней
- Subject Alternative Names: localhost, 127.0.0.1

### Готовые сертификаты

```bash
# Использовать свои сертификаты
exphttp --tls --cert /path/to/cert.pem --key /path/to/key.pem

# Сгенерировать сертификат вручную (Let's Encrypt, mkcert и т.д.)
mkcert localhost 127.0.0.1
exphttp --tls --cert localhost+1.pem --key localhost+1-key.pem
```

### Let's Encrypt

Автоматическое получение доверенных сертификатов (требует установленный [certbot](https://certbot.eff.org/) и открытый порт 80):

```bash
# Получить сертификат и запустить HTTPS
exphttp --letsencrypt --domain example.com -p 443

# С email для уведомлений об истечении
exphttp --letsencrypt --domain example.com --email admin@example.com
```

Сертификат сохраняется в `~/.exphttp/letsencrypt/` и переиспользуется при следующих запусках. Автоматически обновляется, если до истечения осталось менее 30 дней.

#### Установка certbot

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install certbot

# Fedora / RHEL / CentOS
sudo dnf install certbot

# Arch Linux
sudo pacman -S certbot

# macOS (Homebrew)
brew install certbot

# pip (любая ОС)
pip install certbot
```

> Если certbot не установлен или OpenSSL недоступен для самоподписанного
> сертификата, запуск с TLS завершится ошибкой. Это сделано намеренно, чтобы
> не снижать уровень защиты молча.

### cURL с самоподписным сертификатом

```bash
# Игнорировать проверку сертификата
curl -k https://localhost:8080/

# Или добавить сертификат
curl --cacert cert.pem https://localhost:8080/
```

## Basic Auth

HTTP Basic Authentication для защиты доступа.

### Режимы аутентификации

```bash
# Фиксированные credentials
exphttp --auth admin:mysecretpassword

# Случайные credentials (выведет в консоль)
exphttp --auth random

# Фиксированный username, случайный пароль
exphttp --auth admin
```

### Использование с cURL

```bash
# С credentials в URL
curl -u admin:password https://localhost:8080/

# Или через заголовок
curl -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ=" https://localhost:8080/
```

### Программное использование

```python
from src import ExperimentalHTTPServer, BasicAuthenticator

# Кастомная аутентификация
def check_user(username, password):
    return username == "admin" and password == "secret"

auth = BasicAuthenticator(auth_callback=check_user)
server = ExperimentalHTTPServer(host="0.0.0.0", port=443, tls=True)
server.authenticator = auth
server.start()
```

## Область доступа uploads/

Сервер всегда ограничивает пользовательские файловые операции рабочей папкой `uploads/` внутри выбранного `--dir`:

- `GET` — встроенный `index.html`, `/static/...` и файлы из `uploads/`
- `FETCH`, `INFO` — только uploads/
- `POST`, `PUT`, `PATCH`, `NONE`, продвинутая загрузка — запись только в uploads/
- `DELETE`, `SMUGGLE` — работа только с uploads/
- Защита от path traversal (`../`)
- `static/` — доступна только для чтения (JS, CSS, изображения)

## HTML Smuggling

Метод `SMUGGLE` генерирует самодостаточную HTML-страницу с файлом, встроенным в Base64. При открытии в браузере файл автоматически скачивается — данные не передаются по сети повторно, а извлекаются из самого HTML.

### Зачем

- Обход DLP/прокси, которые блокируют прямое скачивание бинарных файлов
- Передача файлов через каналы, где доступен только HTML (email, мессенджеры)
- Одноразовые ссылки — временный HTML-файл удаляется после первого GET-запроса

### Параметры

| Параметр (query string) | Описание |
|--------------------------|----------|
| `encrypt=1` | Включить XOR-шифрование (пароль генерируется на сервере) |

При шифровании (`encrypt=1`):
- Сервер генерирует случайный 7-символьный пароль (A-Z, 0-9)
- Пароль отображается как CAPTCHA-изображение на странице скачивания
- Пользователь вводит пароль для расшифровки файла в браузере (CryptoJS SHA256 + XOR)

### Пример

```bash
# Создать HTML Smuggling страницу для файла (без шифрования)
curl -X SMUGGLE http://localhost:8080/uploads/secret.txt
# Ответ: {"url": "/uploads/smuggle_0123abcd4567ef89.html", "file": "secret.txt", "encrypted": false}
# Заголовок: X-Smuggle-URL: /uploads/smuggle_0123abcd4567ef89.html

# С шифрованием
curl -X SMUGGLE "http://localhost:8080/uploads/secret.txt?encrypt=1"
# Ответ: {"url": "/uploads/smuggle_fedcba9876543210.html", "file": "secret.txt", "encrypted": true}
# Заголовок: X-Smuggle-URL: /uploads/smuggle_fedcba9876543210.html

# Скачать HTML-страницу (файл удалится автоматически после отдачи)
curl http://localhost:8080/uploads/smuggle_0123abcd4567ef89.html -o smuggle.html
```

### Автоматическая очистка

- Временные HTML-файлы (`smuggle_*.html`) удаляются после первого GET/HEAD-запроса или совпавшего conditional-запроса
- При перезапуске сервера все оставшиеся `smuggle_*.html` в `uploads/` очищаются автоматически
- Исходный файл для SMUGGLE ограничен меньшим из лимита SMUGGLE (по умолчанию 10 MiB) и общего лимита загрузки; превышение возвращает JSON `413` без создания временной HTML-страницы

## Утилита расшифровки

CLI инструмент для работы с XOR-шифрованием:

```bash
# Расшифровать файл
python tools/decrypt.py uploads/abc123.bin mypassword

# Расшифровать с сохранением в файл
python tools/decrypt.py uploads/abc123.bin mypassword -o decrypted.txt

# Зашифровать файл
python tools/decrypt.py secret.txt mypassword -e -o secret.enc

# Пакетная расшифровка всех файлов
python tools/decrypt.py uploads/ mypassword --all

# Расшифровать только .bin файлы
python tools/decrypt.py uploads/ mypassword --all -p "*.bin"

# Тихий режим (без вывода в консоль)
python tools/decrypt.py uploads/file.bin pass -q
```

### Опции decrypt.py

| Опция | Описание |
|-------|----------|
| `-o, --output FILE` | Выходной файл |
| `-e, --encrypt` | Режим шифрования (по умолчанию: расшифровка) |
| `-a, --all` | Обработать все файлы в директории |
| `-p, --pattern PAT` | Паттерн файлов (по умолчанию: `*`) |
| `-q, --quiet` | Тихий режим |
| `-h, --help` | Показать справку |

## Использование как библиотеки

```python
from src import ExperimentalHTTPServer, xor_encrypt, xor_decrypt

# Запуск сервера
server = ExperimentalHTTPServer(
    host="127.0.0.1",
    port=8080,
    root_dir="./data"
)
server.start()  # Блокирующий вызов

# Шифрование данных
encrypted = xor_encrypt(b"Hello World", "password")
decrypted = xor_decrypt(encrypted, "password")
assert decrypted == b"Hello World"
```

## API примеры

### cURL

```bash
# GET — получить файл
curl http://localhost:8080/index.html

# PING — проверка сервера
curl -X PING http://localhost:8080/

# INFO — метаданные файла
curl -X INFO http://localhost:8080/uploads/

# FETCH — скачать файл
curl -X FETCH http://localhost:8080/uploads/test.txt -o test.txt

# Очистить uploads/ (скрытые служебные файлы сохраняются)
curl -X DELETE "http://localhost:8080/uploads?clear=1"

# Очистить заметки отдельно от uploads/
curl -X NOTE "http://localhost:8080/notes?clear=1"

# NONE — загрузить файл
curl -X NONE -H "X-File-Name: test.txt" \
  --data-binary @test.txt http://localhost:8080/

# PUT — альтернативная загрузка
curl -X PUT -H "X-File-Name: data.bin" \
  --data-binary @data.bin http://localhost:8080/

# POST — загрузка файла как NONE
curl -X POST -H "X-File-Name: post.txt" \
  --data-binary @post.txt http://localhost:8080/

# Загрузка (продвинутая)
curl -X CHECKDATA -H "Content-Type: application/json" \
  -d '{"d":"SGVsbG8gV29ybGQ=","n":"hello.txt"}' \
  http://localhost:8080/
```

### JavaScript (браузер)

```javascript
// Кастомный метод PING
const xhr = new XMLHttpRequest();
xhr.open('PING', 'http://localhost:8080/', true);
xhr.onload = () => console.log(JSON.parse(xhr.responseText));
xhr.send();

// Загрузка файла через NONE
async function uploadFile(file) {
    const response = await fetch('http://localhost:8080/', {
        method: 'NONE',
        headers: { 'X-File-Name': file.name },
        body: file
    });
    return response.json();
}

// Продвинутая загрузка текстового payload
async function advancedUpload(data, filename) {
    const base64 = btoa(data);

    const response = await fetch('http://localhost:8080/', {
        method: 'CHECKDATA',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ d: base64, n: filename })
    });
    return response.json();
}
```

### Python (requests)

```python
import requests
import base64

# PING
response = requests.request('PING', 'http://localhost:8080/')
print(response.json())

# INFO о директории uploads
response = requests.request('INFO', 'http://localhost:8080/uploads/')
print(response.json())

# Загрузка файла через NONE
with open('test.txt', 'rb') as f:
    response = requests.request(
        'NONE',
        'http://localhost:8080/',
        data=f.read(),
        headers={'X-File-Name': 'test.txt'}
    )
print(response.json())

# Продвинутая загрузка: используйте любой нестандартный метод с payload
data = base64.b64encode(b"Secret data").decode()
response = requests.request(
    'CHECKDATA',
    'http://localhost:8080/',
    json={'d': data, 'n': 'secret.txt'},
    headers={'Content-Type': 'application/json'}
)
print(response.json())
```

## Безопасность

### Встроенные меры защиты

- **TLS/HTTPS** — шифрование трафика с TLS 1.2+
- **Basic Auth** — аутентификация с PBKDF2-SHA256 (600K итераций) + rate limiting
- **Path Traversal** — проверка `resolve()` + `Path.relative_to()` + блокировка symlinks
- **Санитизация имён** — удаление опасных символов из имён файлов
- **CORS** — настроенные заголовки для кросс-доменных запросов
- **Доступ только к uploads/** — ограничение пользовательских файловых операций
- **Таймауты** — защита от Slowloris (30s заголовки, 300s тело)
- **Лимит размера** — ограничение размера загружаемых файлов (413 Payload Too Large)
- **Скрытые файлы** — любые path-сегменты с leading dot, включая dotfiles в `uploads/`, недоступны через GET и INFO
- **User content hardening** — загруженные HTML/SVG отдаются как attachment, а ответы получают `X-Content-Type-Options: nosniff`
- **HMAC** — опциональная проверка целостности данных в продвинутой загрузке

### Ограничения XOR-шифрования

XOR-шифрование используется для **обфускации**, а не криптографической защиты:

- Уязвим к частотному анализу
- Повторяющийся ключ легко восстановить
- Нет аутентификации данных

Для реальной защиты рекомендуется использовать AES-GCM или ChaCha20-Poly1305.

## Технические детали

- **Socket timeout**: 5 секунд (per-recv), 30s headers, 300s body
- **Chunk size**: 65536 байт (64 KB) для приёма и стриминга файлов
- **Backlog**: 128 соединений
- **HTTP версия**: 1.1
- **Кодировка**: UTF-8
- **Worker threads**: 10 (по умолчанию)
- **Max upload**: 100 MB (по умолчанию)
- **TLS**: TLS 1.2+ с ECDHE+AESGCM шифрами
- **Версия**: 2.0.0

## Разработка

### Установка для разработки

```bash
# Базовая установка
pip install -e .

# Базово для pytest
pip install -e ".[dev]"

# С линтерами
pip install -e ".[lint]"

# Локально как в CI (pytest + hypothesis + benchmark + mypy + ruff + crypto)
pip install -e ".[crypto,dev,lint,test]"

# Документация сайта
pip install -e ".[docs]"

# Всё вместе
pip install -e ".[all]"
```

Для воспроизводимой установки теми же версиями инструментов, что и в CI,
security workflow и Docker wheel build, используйте общий constraints-файл:

```bash
PIP_CONSTRAINT=constraints/ci.txt pip install -e ".[crypto,dev,lint,test]"
```

`Dockerfile` теперь также фиксирует базовый образ `python:3.12-slim` по digest.
Обновить pin можно так:

```bash
docker buildx imagetools inspect python:3.12-slim --format '{{json .Manifest.Digest}}'
```

`README.md` остаётся корневым guide-файлом, а `docs/index.md`,
`docs/architecture.md`, `docs/threat-model.md` и `docs/ADR/*` живут как
страницы MkDocs. Зеркальные пары `API.md` -> `docs/api.md`,
`CHANGELOG.md` -> `docs/changelog.md`, `CONTRIBUTING.md` ->
`docs/contributing.md` и `SECURITY.md` -> `docs/security.md`
генерируются через `tools/sync_docs.py`.

### Тестирование

```bash
# Запуск тестов
pytest

# С покрытием
pytest --cov=src

# Конкретный тест
pytest tests/test_http/test_request.py

# Минимальный browser smoke (нужен Node.js/npm с npx)
python tools/browser_smoke.py
```

### Проверка кода

```bash
# Линтер
ruff check src tests

# Форматирование
ruff format --check src tests

# Статическая типизация
mypy src

# Проверка зеркальных Markdown-файлов
python tools/sync_docs.py --check

# Пересборка docs/ из root-canonical файлов
python tools/sync_docs.py --write

# Сборка сайта документации
mkdocs build --strict
```

## Лицензия

MIT
