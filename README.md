# Experimental HTTP Server

![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)

HTTP-сервер с поддержкой произвольных HTTP-методов, написанный на чистом Python без внешних зависимостей.

## Возможности

- Кастомные HTTP-методы: `GET`, `POST`, `PUT`, `FETCH`, `INFO`, `PING`, `NONE`, `OPTIONS`
- Загрузка файлов через методы `NONE` и `PUT`
- Скачивание файлов через метод `FETCH` с заголовками для загрузки
- Получение метаданных файлов/директорий через `INFO` (JSON)
- **HTTPS/TLS** — самоподписные сертификаты на лету или свои
- **Basic Auth** — HTTP аутентификация с генерацией паролей
- **OPSEC-режим** — случайные имена методов + XOR-шифрование + HMAC
- **Sandbox-режим** — ограничение доступа только к `uploads/`
- **Многопоточность** — ThreadPoolExecutor для параллельной обработки
- Ограничение размера загрузки (по умолчанию 100 MB)
- Веб-интерфейс с drag & drop загрузкой
- Модульная архитектура (mixin-паттерн)
- Поддержка кириллических имён файлов

## Требования

- Python 3.10 — 3.14 (используются type hints с `|` синтаксисом)
- Стандартная библиотека (без внешних зависимостей для runtime)
- OpenSSL (опционально, для генерации TLS сертификатов)
- Typed package (PEP 561) — поддержка статической типизации

## Быстрый старт

```bash
pip install -e .
exphttp --open
```

Сервер запустится на `http://127.0.0.1:8080` и откроет браузер.

Полезные комбинации:
```bash
exphttp --tls --auth random    # HTTPS + авто-пароль
exphttp --opsec --sandbox      # Скрытный + ограниченный режим
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
│   ├── server.py          # ExperimentalHTTPServer
│   ├── config.py          # ServerConfig
│   ├── exceptions.py      # Кастомные исключения
│   ├── py.typed           # PEP 561 marker
│   │
│   ├── http/              # HTTP модули
│   │   ├── request.py     # HTTPRequest
│   │   ├── response.py    # HTTPResponse
│   │   └── utils.py       # Утилиты (sanitize, etc)
│   │
│   ├── handlers/          # Обработчики методов
│   │   ├── base.py        # BaseHandler
│   │   ├── files.py       # GET, POST, PUT, FETCH, NONE
│   │   ├── info.py        # INFO, PING
│   │   ├── opsec.py       # OPSEC upload
│   │   └── smuggle.py     # HTML Smuggling
│   │
│   ├── security/          # Безопасность
│   │   ├── auth.py        # Basic Auth
│   │   ├── crypto.py      # XOR/HMAC
│   │   └── tls.py         # TLS сертификаты
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
│   └── decrypt.py
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
| `-o, --opsec` | Включить OPSEC-режим | выключен |
| `-s, --sandbox` | Включить Sandbox-режим | выключен |
| `-m, --max-size MB` | Макс. размер загрузки в MB | `100` |
| `-w, --workers N` | Количество worker потоков | `10` |
| `-q, --quiet` | Тихий режим (минимум логов) | выключен |
| `--debug` | Debug режим (подробное логирование) | выключен |
| `--open` | Открыть в браузере после запуска | выключен |
| `--tls` | Включить HTTPS (самоподписный сертификат) | выключен |
| `--cert FILE` | Путь к сертификату (PEM) | - |
| `--key FILE` | Путь к приватному ключу (PEM) | - |
| `--letsencrypt` | Получить сертификат Let's Encrypt | выключен |
| `--domain DOMAIN` | Домен для Let's Encrypt | - |
| `--email EMAIL` | Email для Let's Encrypt уведомлений | - |
| `--auth USER:PASS` | Включить Basic Auth | выключен |
| `--auth random` | Сгенерировать случайные credentials | - |
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

# OPSEC-режим (случайные имена методов)
exphttp --opsec

# Sandbox-режим (доступ только к uploads/)
exphttp --sandbox

# Полная защита: TLS + Auth + OPSEC + Sandbox
exphttp --tls --auth random --opsec --sandbox

# Комбинированный режим
exphttp -H 0.0.0.0 -p 8080 -d ./data --opsec --sandbox -m 200
```

## HTTP-методы

| Метод | Описание | Sandbox |
|-------|----------|---------|
| `GET` | Получение файлов и страниц | Корневые файлы + uploads/ + static/ |
| `POST` | Загрузка файлов на сервер | Да |
| `PUT` | Загрузка файлов на сервер | Да |
| `OPTIONS` | CORS preflight | Да |
| `FETCH` | Скачивание файлов с Content-Disposition | Только uploads/ |
| `INFO` | Метаданные файла/директории (JSON) | Только uploads/ |
| `PING` | Проверка доступности сервера | Да |
| `NONE` | Загрузка файлов на сервер | Да |
| `SMUGGLE` | HTML Smuggling — генерация страницы со встроенным файлом | Только uploads/ |

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

## Веб-интерфейс

Откройте `http://localhost:8080` в браузере. Вкладки:

1. **Запросы** — отправка GET/POST/FETCH/INFO/PING
2. **Загрузка файлов (NONE)** — drag & drop интерфейс
3. **OPSEC Mode** — зашифрованная загрузка
4. **Файлы на сервере** — просмотр uploads/

## OPSEC-режим

Режим повышенной скрытности для передачи файлов:

### Особенности

- **Случайные имена методов** — при каждом запуске генерируются новые
- **Скрытые имена файлов** — имя не передаётся в URL/заголовках
- **Base64-кодирование** — данные в теле запроса как JSON
- **XOR-шифрование** — опциональное шифрование перед передачей
- **Хеш-именование** — файлы сохраняются с SHA256-хешем вместо имени

### Генерируемые методы

При запуске с `--opsec` создаётся `.opsec_config.json`:

```json
{
  "upload": "VALIDATESTATUS",
  "download": "SYNCRECORD",
  "info": "QUERYRECORD",
  "ping": "CHECKDATA"
}
```

Имена формируются из комбинаций:
- Префиксы: CHECK, SYNC, VERIFY, UPDATE, QUERY, REPORT, SUBMIT, VALIDATE, PROCESS, EXECUTE
- Суффиксы: DATA, STATUS, INFO, CONTENT, RESOURCE, ITEM, OBJECT, RECORD, ENTRY

### Формат OPSEC-запроса

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

### Пример OPSEC загрузки

```bash
# 1. Зашифровать файл локально
python tools/decrypt.py secret.txt mykey -e -o secret.enc

# 2. Закодировать в Base64
base64 secret.enc > secret.b64

# 3. Отправить с произвольным методом (имя метода игнорируется в OPSEC)
curl -X SYNCDATA -H "Content-Type: application/json" \
  -d '{"d":"'$(cat secret.b64)'","n":"secret.txt","e":"xor","k":"mykey"}' \
  http://localhost:8080/
```

### Ответ OPSEC

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

> Если certbot не установлен, сервер выведет предупреждение и автоматически переключится на самоподписный сертификат.

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

## Sandbox-режим

Ограничивает доступ к файловой системе:

- `GET` — корневые файлы (index.html и т.д.) + uploads/ + static/
- `FETCH`, `INFO` — только uploads/
- Защита от path traversal (`../`)
- `static/` — доступна только для чтения (JS, CSS, изображения)

```bash
exphttp --sandbox
```

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
# Ответ: {"url": "/uploads/smuggle_abc123.html", "file": "secret.txt", "encrypted": false}

# С шифрованием
curl -X SMUGGLE "http://localhost:8080/uploads/secret.txt?encrypt=1"
# Ответ: {"url": "/uploads/smuggle_def456.html", "file": "secret.txt", "encrypted": true}

# Скачать HTML-страницу (файл удалится автоматически после отдачи)
curl http://localhost:8080/uploads/smuggle_abc123.html -o smuggle.html
```

### Автоматическая очистка

- Временные HTML-файлы (`smuggle_*.html`) удаляются после первого GET-запроса
- При перезапуске сервера все оставшиеся `smuggle_*.html` в `uploads/` очищаются автоматически

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
    root_dir="./data",
    opsec_mode=True,
    sandbox_mode=True
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

# NONE — загрузить файл
curl -X NONE -H "X-File-Name: test.txt" \
  --data-binary @test.txt http://localhost:8080/

# PUT — альтернативная загрузка
curl -X PUT -H "X-File-Name: data.bin" \
  --data-binary @data.bin http://localhost:8080/

# POST — echo данных
curl -X POST -d "test data" http://localhost:8080/

# OPSEC загрузка (в OPSEC-режиме)
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

// OPSEC загрузка с шифрованием (требует crypto-js)
async function opsecUpload(data, filename, key) {
    const encrypted = CryptoJS.AES.encrypt(data, key); // или XOR
    const base64 = btoa(encrypted);

    const response = await fetch('http://localhost:8080/', {
        method: 'SYNCDATA',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ d: base64, n: filename, e: 'xor', k: key })
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

# OPSEC загрузка
data = base64.b64encode(b"Secret data").decode()
response = requests.post(
    'http://localhost:8080/',
    json={'d': data, 'n': 'secret.txt'},
    headers={'Content-Type': 'application/json'}
)
print(response.json())
```

## Безопасность

### Встроенные меры защиты

- **TLS/HTTPS** — шифрование трафика с TLS 1.2+
- **Basic Auth** — аутентификация с хешированием паролей (SHA256 + salt)
- **Path Traversal** — проверка `resolve()` + валидация префикса пути
- **Санитизация имён** — удаление опасных символов из имён файлов
- **CORS** — настроенные заголовки для кросс-доменных запросов
- **Sandbox** — ограничение доступа к файловой системе
- **Таймауты** — защита от медленных HTTP атак (1 сек)
- **Лимит размера** — ограничение размера загружаемых файлов (413 Payload Too Large)
- **Скрытые файлы** — `.opsec_config.json`, `.env`, `.gitignore` недоступны через GET
- **HMAC** — опциональная проверка целостности данных в OPSEC режиме

### OPSEC маскировка

В OPSEC режиме сервер маскируется:
- Заголовок `Server: nginx` вместо `ExperimentalHTTPServer`
- Скрыты кастомные методы в `Access-Control-Allow-Methods`
- Неизвестные методы возвращают 404 вместо 405
- Минимальное логирование (только ошибки)

### Ограничения XOR-шифрования

XOR-шифрование используется для **обфускации**, а не криптографической защиты:

- Уязвим к частотному анализу
- Повторяющийся ключ легко восстановить
- Нет аутентификации данных

Для реальной защиты рекомендуется использовать AES-GCM или ChaCha20-Poly1305.

## Технические детали

- **Socket timeout**: 1 секунда
- **Chunk size**: 65536 байт (64 KB)
- **Backlog**: 5 соединений
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

# С тестами
pip install -e ".[dev]"

# С линтерами
pip install -e ".[lint]"

# Всё вместе
pip install -e ".[all]"
```

### Тестирование

```bash
# Запуск тестов
pytest

# С покрытием
pytest --cov=src

# Конкретный тест
pytest tests/test_http/test_request.py
```

### Проверка кода

```bash
# Линтер
ruff check src

# Форматирование
ruff format src

# Статическая типизация
mypy src
```

## Лицензия

MIT
