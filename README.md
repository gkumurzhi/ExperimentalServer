# Experimental HTTP Server

![Python 3.10-3.14](https://img.shields.io/badge/Python-3.10--3.14-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)
[![CI](https://github.com/gkumurzhi/ExperimentalServer/actions/workflows/ci.yml/badge.svg)](https://github.com/gkumurzhi/ExperimentalServer/actions/workflows/ci.yml)
[![Security](https://github.com/gkumurzhi/ExperimentalServer/actions/workflows/security.yml/badge.svg)](https://github.com/gkumurzhi/ExperimentalServer/actions/workflows/security.yml)
![Type checked](https://img.shields.io/badge/mypy-strict-blue.svg)
![Lint](https://img.shields.io/badge/ruff-passing-blue.svg)

HTTP-сервер на Python с поддержкой произвольных HTTP-методов, TLS, ACME и защищённых заметок.

📄 **Документация:** [API Reference](API.md) · [Threat Model](docs/threat-model.md) · [ADR](docs/ADR/) · [Security Policy](SECURITY.md) · [Contributing](CONTRIBUTING.md) · [Examples](examples/) · [Docker](Dockerfile)

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

- Кастомные HTTP-методы: базовый surface включает `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`, `FETCH`, `INFO`, `PING`, `NONE`, `OPTIONS`; lab-only surface включает `NOTE` и `SMUGGLE`
- Загрузка файлов через методы `NONE`, `POST`, `PUT`, `PATCH`
- Скачивание файлов через метод `FETCH` с заголовками для загрузки
- Получение метаданных файлов/директорий через `INFO` (JSON)
- **Secure Notepad** — метод `NOTE` с end-to-end шифрованием AES-256-GCM и ECDH P-256
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

- Python 3.10 — 3.14 (эта матрица проверяется в CI; используются type hints с `|` синтаксисом)
- Runtime-зависимости из `pyproject.toml` (`cryptography`, `acme` и их транзитивные пакеты)
- Typed package (PEP 561) — поддержка статической типизации

## Быстрый старт

```bash
pip install -e .
exphttp --open
```

Сервер запустится на `http://127.0.0.1:8080` и откроет браузер. Все пользовательские файлы читаются и записываются через `<root>/uploads/`; встроенный `index.html` и `/static/...` отдаются только для загрузки веб-интерфейса.

Полезные комбинации:
```bash
exphttp --tls --auth random    # HTTPS + авто-пароль в интерактивном терминале
exphttp -d ./data -m 500       # Рабочая папка ./data/uploads, лимит 500 MB
exphttp -H 0.0.0.0 -p 8443 --tls --auth-file ./auth.txt  # Trusted lab; см. режимы ниже
```

## Структура проекта

```
ExperimentalHTTPServer/
├── pyproject.toml         # Конфигурация проекта
├── README.md
├── CLAUDE.md              # Инструкции для AI
│
├── exphttp/               # Публичный import/package entry point
│   ├── __init__.py
│   ├── __main__.py        # python -m exphttp
│   └── cli.py             # CLI entry point
│
├── src/                   # Исходный код
│   ├── __init__.py
│   ├── __main__.py        # compatibility module entry point
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
exphttp [опции]
# или
python -m exphttp [опции]
```

### Параметры командной строки

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--config FILE` | Прочитать настройки из INI-файла (`defaults < config < EXPHTTP_* < CLI`) | - |
| `--check-config` | Проверить итоговую конфигурацию и выйти без запуска сервера | выключен |
| `--print-config` | Напечатать итоговую конфигурацию JSON с редактированием inline-секретов | выключен |
| `--write-sample-config FILE` | Записать пример public-direct INI-конфига и выйти | - |
| `-H, --host HOST` | Хост для привязки | `127.0.0.1` |
| `-p, --port PORT` | Порт для прослушивания | `8080` |
| `-d, --dir DIR` | Корневая директория | `.` |
| `-m, --max-size MB` | Макс. размер тела одного upload-запроса в MB | `100` |
| `--upload-storage-limit MB` | Общий лимит размера `uploads/` в MB (`0` = выключен) | `0` |
| `--upload-file-limit N` | Общий лимит количества файлов в `uploads/` (`0` = выключен) | `0` |
| `--upload-reserve-free MB` | Минимум свободного места на диске при commit загрузки в MB | `0` |
| `--note-storage-limit MB` | Общий лимит encrypted blobs в `notes/` (`0` = выключен) | `256` |
| `--note-count-limit N` | Общий лимит количества заметок (`0` = выключен) | `1000` |
| `--smuggle-temp-age SECONDS` | Максимальный возраст временных SMUGGLE HTML (`0` = выключен) | `3600` |
| `--smuggle-temp-file-limit N` | Лимит количества временных SMUGGLE HTML (`0` = выключен) | `32` |
| `--smuggle-temp-storage-limit MB` | Лимит размера временных SMUGGLE HTML (`0` = выключен) | `128` |
| `--max-header-size KB` | Макс. размер HTTP request headers в KiB | `64` |
| `--body-memory-budget MB` | Aggregate лимит in-flight тел запросов в памяти | `workers * max-size` |
| `--body-idle-timeout SECONDS` | Макс. пауза между chunk-ами тела запроса (`0` = выключен) | `5` |
| `--body-timeout SECONDS` | Общий deadline на прием тела после заголовков (`0` = выключен) | `300` |
| `--body-min-rate BYTES_PER_SECOND` | Мин. средняя скорость приема тела (`0` = выключен) | `0` |
| `--stream-send-idle-timeout SECONDS` | Макс. блокировка отправки одного chunk streamed-ответа | `5` |
| `--stream-send-timeout SECONDS` | Общий deadline streamed-ответа (`0` = выключен) | `300` |
| `--max-websocket-connections N` | Макс. активных WebSocket соединений (`0` = отклонять все) | `workers // 2` |
| `--websocket-frame-idle-timeout SECONDS` | Макс. пауза при ожидании продолжения неполного WebSocket frame | `5` |
| `-w, --workers N` | Количество worker потоков | `10` |
| `-q, --quiet` | Тихий режим (минимум логов) | выключен |
| `--debug` | Debug режим (подробное логирование) | выключен |
| `--open` | Открыть в браузере после запуска | выключен |
| `--json-log` | Структурированный JSON формат логов | выключен |
| `--cors-origin ORIGIN` | Разрешить CORS; точный origin также допускает browser-origin mutations | выключен |
| `--profile {serve,workspace,lab}` | Набор возможностей сервера | `workspace` |
| `--advanced-upload` | Устаревший alias для `--profile lab` | - |
| `--tls` | Включить HTTPS (самоподписный сертификат) | выключен |
| `--cert FILE` | Путь к сертификату (PEM) | - |
| `--key FILE` | Путь к приватному ключу (PEM) | - |
| `--letsencrypt` | Получить сертификат Let's Encrypt | выключен |
| `--domain DOMAIN` | Домен для Let's Encrypt | - |
| `--email EMAIL` | Email для Let's Encrypt уведомлений | - |
| `--sslip` | Получить Let's Encrypt сертификат для `<public-ip>.sslip.io` | выключен |
| `--public-ip IP` | Публичный IPv4 для `--sslip` (иначе автоопределение) | - |
| `--acme-staging` | Использовать Let's Encrypt staging | выключен |
| `--acme-server URL` | Пользовательский ACME directory URL | - |
| `--acme-http-address ADDR` | Адрес HTTP-01 challenge server | все интерфейсы |
| `--acme-http-port PORT` | Порт HTTP-01 challenge server | `80` |
| `--auth USER:PASS` | Включить Basic Auth через argv; только для локального интерактивного запуска | выключен |
| `--auth-file FILE` | Включить Basic Auth из файла с одной строкой `user:password` | выключен |
| `--auth random` | Сгенерировать случайные credentials в интерактивном терминале | - |
| `--help` | Показать справку | - |

### Профили возможностей

CLI default — `workspace`: обычная рабочая папка файлов с загрузкой и
удалением отдельных файлов, но без экспериментальных lab-only возможностей.
Поддерживаемое направление зафиксировано в
[ADR-006](docs/ADR/ADR-006-profile-default-and-exposure.md): `lab` остаётся
явным opt-in для экспериментов и legacy scripts. Если старый сценарий
полагался на implicit `lab`, закрепите совместимость через `--profile lab`
или устаревший alias `--advanced-upload`.

| Профиль | Первый выбор для | Методы и возможности |
|---------|------------------|----------------------|
| `serve` | Read-only sharing или просмотр файлов без мутаций. | Только чтение: `GET`, `HEAD`, `OPTIONS`, `FETCH`, `INFO`, `PING`. Загрузка, удаление, `NOTE`, `SMUGGLE`, WebSocket и advanced upload отключены. |
| `workspace` | Нормальная рабочая папка файлов; default для новых запусков. | `serve` + обычная загрузка (`POST`, `PUT`, `PATCH`, `NONE`) и удаление отдельных файлов через `DELETE`. Очистка `uploads/`, `NOTE`, `SMUGGLE`, WebSocket и advanced upload отключены. |
| `lab` | Явные эксперименты и scripts, которым нужны нестандартные методы или полный legacy surface. | Совместимый экспериментальный режим: все методы, advanced upload, `SMUGGLE`, `NOTE`, WebSocket и операции очистки включены явно. |

`PING` возвращает активный `profile`, `supported_methods` и карту
`capabilities`; CORS preflight и браузерный UI используют эти же данные.

### Конфигурационные файлы

Для серверов без GUI предпочтителен INI-конфиг:

```bash
exphttp --write-sample-config /etc/exphttp/exphttp.ini
exphttp --config /etc/exphttp/exphttp.ini --check-config
exphttp --config /etc/exphttp/exphttp.ini
```

Поддерживаемый precedence: built-in defaults < INI-файл < переменные
`EXPHTTP_*` < явно переданные CLI-флаги. `--print-config` показывает
нормализованные настройки без inline-секретов, что удобно для проверки systemd
или container окружения.

Для public-direct конфигураций включайте `public_direct = true`: валидатор
требует real TLS (`sslip`, `letsencrypt` или готовые `cert_file`/`key_file`),
`auth_file`, `profile = workspace|serve`, явный `body_memory_budget_mb`,
включённые body/stream timeouts и запрещает wildcard CORS для такого режима.
Плагины в public-direct режиме отключены, пока в `[plugins]` явно не задано
`allow_public_direct = true`.

### Примеры запуска

```bash
# Стандартный запуск (localhost:8080)
exphttp

# Совместимость со старым experimental/lab surface
exphttp --profile lab

# HTTPS с самоподписным сертификатом
exphttp --tls

# HTTPS с Basic Auth (случайные credentials в интерактивном терминале)
exphttp --tls --auth random

# HTTPS с своими credentials для локального интерактивного запуска
exphttp --tls --auth admin:secretpassword

# HTTPS с credentials из файла; предпочтительно для services/containers/CI
exphttp --tls --auth-file ./auth.txt

# HTTPS с готовыми сертификатами
exphttp --tls --cert cert.pem --key key.pem

# Внешний доступ для доверенной сети: минимум TLS + Auth из secret file
exphttp -H 0.0.0.0 -p 443 --tls --auth-file /run/secrets/exphttp_auth

# Комбинированный режим
exphttp -H 0.0.0.0 -p 8080 -d ./data --tls --auth-file ./auth.txt -m 200
```

### Режимы эксплуатации

- **Localhost** — режим по умолчанию: `exphttp` слушает `127.0.0.1:8080` и
  подходит для локальных экспериментов без внешнего доступа.
- **Trusted lab** — для контролируемой лабораторной сети можно явно указать
  `-H 0.0.0.0`, но включайте TLS и Basic Auth, используйте отдельный `--dir`
  и ограничивайте доступ firewall/NAT.
- **External exposure** — привязка к `0.0.0.0`, TLS и Auth не делает сервис
  безопасным для произвольного интернета. Для такого режима нужны как минимум
  реальный сертификат, сильные credentials из secret-хранилища через
  `--auth-file`, reverse proxy с rate limiting и request-size limits,
  мониторинг, firewall allowlist и точный `--cors-origin` для доверенного
  браузерного UI. Не используйте
  `--cors-origin *` для публичного браузерного интерфейса. App-side Basic
  Auth rate limiting считает неудачи по direct TCP peer IP; за reverse proxy
  настройте proxy-side per-client throttling, потому что приложение пока не
  доверяет `Forwarded`/`X-Forwarded-For`.

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
| `NOTE` | Защищённый блокнот (ECDH + AES-256-GCM) | Только notes/ |
| `SMUGGLE` | HTML Smuggling — генерация страницы со встроенным файлом | Только uploads/ |
| Любой нестандартный метод с payload | Загрузка (продвинутая) через `d`/`data`, `X-D` или `?d=` | `uploads/` |

Доступность методов зависит от `--profile`; таблица выше описывает полный
набор режима `lab`. Текущий HTTP/WebSocket surface считается legacy v0:
клиентам следует определять доступные методы и возможности через `PING`
(`profile`, `supported_methods`, `capabilities`) и сверяться с
[API Reference](API.md) перед тем, как полагаться на детали ошибок, retry или
Notepad/WebSocket semantics. `/api/v1` пока не реализован.

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
| `X-Request-Id` | Ответы после dispatch | 8-символьный hex ID для корреляции логов; прямые ошибки framing/auth/WebSocket upgrade могут вернуться до этой стадии |
| `Content-Security-Policy` | GET (HTML) | CSP заголовок для HTML ответов |

## Веб-интерфейс

Откройте `http://localhost:8080` в браузере. Вкладки:

1. **Запросы** — отправка `GET`, `FETCH`, `INFO`, `PING` по произвольному пути
2. **Загрузка файлов** — drag & drop интерфейс с переключателем метода `POST` / `NONE` / `PUT` / `PATCH`
3. **Загрузка (продвинутая)** — загрузка через JSON body, заголовки или URL-параметры, с опциональным XOR-шифрованием; доступна только в `--profile lab`
4. **Скачивание** — обзор `uploads/`, переход по директориям, `INFO`, `FETCH`, удаление файлов; `SMUGGLE` и быстрая очистка `uploads/` доступны только в `--profile lab`
5. **Secure Notepad** — ECDH/AES-GCM блокнот с автошифрованием и переключением транспорта `HTTP` / `WebSocket`; доступен только в `--profile lab`

## Продвинутая загрузка

Продвинутый сценарий загрузки доступен только в `--profile lab`. В профиле
`workspace` по умолчанию неизвестные HTTP-методы отклоняются, даже если в них
есть advanced-upload payload. Для legacy scripts запустите сервер с
`--profile lab` или устаревшим alias `--advanced-upload`.

### Особенности

- **Legacy lab-only surface** — неизвестные HTTP-методы с payload обрабатываются как продвинутая загрузка только в `--profile lab`
- **Несколько транспортов** — payload можно передать через JSON body, HTTP headers или URL query
- **Base64-кодирование** — данные передаются как `d` / `data`
- **XOR** — при наличии ключа payload можно обфусцировать перед передачей
- **Имя файла опционально** — если `n` / `name` не передано, сервер сохранит `<sha256[:12]>.bin`; любое сохранённое имя при коллизии получает случайный суффикс

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
| `n` / `name` | Имя файла | нет (генерируется SHA256[:12].bin; при коллизии сохранённого имени добавляется случайный суффикс) |
| `e` | Тип шифрования (`xor`) | нет |
| `k` | Ключ для расшифровки на сервере | нет |
| `h` / `hmac` | HMAC-SHA256 для проверки целостности | нет |

### HMAC проверка целостности

Для защиты от повреждения данных можно передать HMAC:

```python
from exphttp import xor_encrypt_with_hmac
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

Сервер проверит HMAC по переданным payload bytes перед расшифровкой и вернёт ошибку если данные повреждены. HMAC не покрывает filename/transport metadata.

### Пример продвинутой загрузки

Требуется `--profile lab` или устаревший alias `--advanced-upload`.

```bash
# 1. Зашифровать файл локально
python tools/decrypt.py secret.txt mykey -e -o secret.enc

# 2. Закодировать в Base64
base64 secret.enc > secret.b64

# 3. Отправить payload нестандартным методом
curl -X CHECKDATA -H "Content-Type: application/json" \
  -d '{"d":"'$(cat secret.b64)'","n":"secret.txt","e":"xor","k":"mykey"}' \
  http://localhost:8080/
```

### Ответ

```json
{
  "ok": true,
  "id": "a1b2c3d4e5f67890",
  "sz": 1234,
  "transport": "body"
}
```

Ответ продвинутой загрузки не содержит фактический путь или сохранённое имя файла. Если клиенту нужно предсказуемо обращаться к файлу после загрузки, передайте `n` / `name` и проверьте результат через `INFO`; имена очищаются, а при конфликте сервер может сохранить файл с суффиксом.

## HTTPS/TLS

Сервер поддерживает HTTPS с автоматической генерацией самоподписных сертификатов.

### Автоматическая генерация

```bash
# Генерирует временный сертификат
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

Автоматическое получение доверенных сертификатов через встроенный ACME-клиент (требуется, чтобы внешний порт 80 доходил до HTTP-01 challenge server):

```bash
# Получить сертификат и запустить HTTPS
exphttp --letsencrypt --domain example.com -p 443

# С email для уведомлений об истечении
exphttp --letsencrypt --domain example.com --email admin@example.com

# Быстрый валидный HTTPS для текущего публичного IPv4 через sslip.io
exphttp --sslip -H 0.0.0.0 -p 443

# Тестовый выпуск без production rate limits
exphttp --letsencrypt --domain example.com --acme-staging
```

Сертификат сохраняется в `~/.exphttp/acme/` и переиспользуется при следующих запусках. Старые сертификаты из `~/.exphttp/letsencrypt/` читаются для совместимости, но новые выпуски пишутся только в `~/.exphttp/acme/`. Автоматическое обновление происходит при старте, если до истечения осталось менее 30 дней.

Если явно запрошен `--letsencrypt` или `--sslip`, ошибка ACME не заменяется самоподписанным сертификатом: запуск завершится ошибкой, чтобы не снижать уровень защиты молча. Wildcard-сертификаты и DNS-01 challenge в этой версии не поддерживаются.

### Linux systemd

`deploy/systemd/` содержит first-class путь для консольных Linux серверов:
`exphttp.service`, `exphttp.ini.example`, `exphttp.env.example` и
`install-systemd.sh`. Скрипт создаёт non-root пользователя `exphttp`, venv в
`/opt/exphttp`, состояние в `/var/lib/exphttp`, конфиг в `/etc/exphttp` и
systemd unit с `ExecStartPre=... --check-config`.

```bash
sudo deploy/systemd/install-systemd.sh
sudo editor /etc/exphttp/exphttp.ini
sudo systemctl enable --now exphttp
journalctl -u exphttp -f
```

По умолчанию пример — public-direct HTTPS (`sslip`) с Basic Auth из
`/etc/exphttp/auth`, `workspace` profile и явным memory budget. Для домена
замените `sslip = true` на `letsencrypt = true` и `domain = files.example.com`.

### Docker и sslip/ACME

`Dockerfile` и `examples/docker/docker-compose.yml` остаются локальными
operator examples. Для опубликованного image используйте
`deploy/docker/docker-compose.public-direct.yml`: он тянет
`ghcr.io/gkumurzhi/exphttp`, монтирует INI-конфиг, Basic Auth secret, `/data`
и ACME state volume, а приложение запускает через `--config`.

```bash
cd deploy/docker
mkdir -p secrets
printf 'admin:<strong-password>\n' > secrets/exphttp_auth
chmod 644 secrets/exphttp_auth
docker compose -f docker-compose.public-direct.yml up -d
```

Compose public-direct preset публикует host `80` -> container `8080` для
HTTP-01 challenge и host `443` -> container `8443` для HTTPS. Проверьте
`exphttp.ini.example` перед запуском: для production лучше задать `domain` или
`public_ip`, включить firewall allowlist где возможно и подобрать Docker
resource limits под `body_memory_budget_mb`.

Локальные примеры ниже собирают image `exphttp:local`; rollback локального
container deployment остаётся operator-owned возвратом к предыдущему
проверенному image/digest. Для published GHCR tags rollback выполняйте на
предыдущий проверенный digest.

`examples/docker/docker-compose.yml` по умолчанию оставляет прежний безопасный
plain HTTP путь: сервис `exphttp` публикует порт только на
`127.0.0.1:8080:8080`, явно запускает app profile `--profile workspace` и не
запускает ACME. Внутри контейнера процесс всё ещё слушает `0.0.0.0`, чтобы
работали Compose-сети и reverse proxy. Для read-only контейнера можно заменить
app profile на `serve`; `lab` используйте только для контролируемых
экспериментов с TLS/Auth/firewall controls. Для локального TLS + Basic Auth
используйте Compose service profile `auth-tls` и secret file:

```bash
mkdir -p examples/docker/secrets
printf 'admin:<strong-password>\n' > examples/docker/secrets/exphttp_auth
chmod 644 examples/docker/secrets/exphttp_auth
docker compose -f examples/docker/docker-compose.yml --profile auth-tls up --build exphttp-auth-tls
```

Файл `examples/docker/secrets/exphttp_auth` должен содержать ровно одну строку
`user:password`; каталог `secrets/` игнорируется git. Local Compose
file-backed secrets сохраняют permissions исходного файла, поэтому файл должен
быть читаемым для container UID `10001`. Для более жёсткого локального режима
можно вместо `chmod 644` сделать owner `10001:10001` и mode `0400`. Не
передавайте контейнерные пароли через `--auth user:password`, потому что argv
виден process listings. Для контейнерного HTTPS через `--sslip` используйте
отдельный ACME-профиль; он тоже запускает app profile `workspace` и требует
тот же Basic Auth secret:

```bash
docker compose -f examples/docker/docker-compose.yml --profile acme up --build exphttp-acme
```

Профиль `exphttp-acme` публикует host `80` -> container `8080` для HTTP-01
challenge (`--acme-http-port 8080`) и host `443` -> container `8443` для
HTTPS (`--port 8443`). Внутри контейнера используются высокие порты, поэтому
сохраняются non-root запуск и `cap_drop: [ALL]`; снаружи firewall/NAT всё равно
должен пропускать публичный порт 80 к этому host. Публичный HTTPS endpoint
требует Basic Auth secret из `examples/docker/secrets/exphttp_auth`; для
интернет-доступа всё равно применяйте firewall allowlists, origin policy,
proxy-side per-client throttling и resource limits из `SECURITY.md`. Если перед
контейнером стоит reverse proxy, он должен проксировать
`/.well-known/acme-challenge/` на challenge listener или временно освободить
public port 80.

ACME состояние пишется в домашний каталог пользователя контейнера:
`/home/exphttp/.exphttp/acme/`. Compose-профиль монтирует named volume
`exphttp-acme-state:/home/exphttp/.exphttp`; этот volume содержит ACME account
keys, private keys доменов и `fullchain.pem`, поэтому защищайте и бэкапьте его
как секретный certificate state. Если cached certificate/key pair отсутствует
или не совпадает, сервер сначала попытается выпустить сертификат заново; если
запуск всё равно завершается с unusable cache/private key диагностикой, удалите
только сломанный каталог `/home/exphttp/.exphttp/acme/live/<domain>/` внутри
ACME volume и повторите выпуск. Это соответствует fail-closed проверке пары
`fullchain.pem` / `privkey.pem`: сервер не будет молча переходить на
самоподписанный сертификат.

`--sslip` без `--public-ip` определяет адрес через `https://api.ipify.org`.
Нужен глобально маршрутизируемый IPv4: private, loopback, carrier-grade NAT и
IPv6-only окружения не подходят. За NAT укажите `--public-ip <global-ipv4>`,
если auto-detection видит не тот адрес, и убедитесь, что public port 80 реально
доходит до контейнерного challenge listener. Оставляйте `--acme-http-address`
по умолчанию, чтобы challenge listener слушал все интерфейсы контейнера;
меняйте его только для явной proxy/topology настройки. Перед production
выпуском можно включить `--acme-staging` в Compose-команде, чтобы проверить
route без production rate limits. Для собственного домена замените `--sslip`
на `--letsencrypt --domain example.com`. ACME реализует только HTTP-01:
DNS-01, TLS-ALPN-01 и wildcard-сертификаты не поддерживаются.

Встроенный Docker `HEALTHCHECK` проверяет plain HTTP `PING` на
`http://127.0.0.1:8080/`; default Compose-сервис наследует эту проверку.
Профиль `auth-tls` переопределяет healthcheck на HTTPS `PING` с Basic Auth,
читая credentials из `/run/secrets/exphttp_auth`. Для `--letsencrypt` и
`--sslip` локальная проверка не отражает реальное состояние публичного имени,
HTTP-01 challenge route и certificate chain, поэтому ACME-профиль отключает
image healthcheck. Используйте внешний HTTPS-probe по публичному имени и
проверку `/metrics`, либо задайте собственный Compose healthcheck под вашу
topology.

ACME renewal выполняется на старте, если до истечения сертификата осталось
менее 30 дней. Для long-running контейнеров запланируйте контролируемый
restart до входа сертификата в это окно, например еженедельно, чтобы startup
renewal успел выполниться до expiry.

`stop_grace_period: 20s` в Compose — контейнерный shutdown budget для
операторского рестарта/rollback. Он намеренно короче максимальных 300s
body/stream deadlines: при остановке контейнера длинные передачи могут быть
прерваны, поэтому выполняйте rolling restart или drain на reverse proxy, если
нужно сохранить активные загрузки/скачивания.

### Docker resource sizing

Контейнерная память должна покрывать Python runtime, TLS buffers, worker
threads и aggregate budget тел запросов. Практическое правило: задавайте
`--body-memory-budget` явно и держите Docker `mem_limit` выше этого значения
с запасом 128-256 MiB; если контейнер маленький, уменьшайте `--workers`,
`--max-size` и `--body-memory-budget` вместе. Persistent storage sizing
состоит из двух слоёв: Docker volume/filesystem quota ограничивает реальный
диск, а `--upload-storage-limit`, `--upload-file-limit`,
`--upload-reserve-free`, `--note-storage-limit`, `--note-count-limit` и
SMUGGLE temp retention ограничивают данные на уровне приложения. В
`examples/docker/docker-compose.yml` есть закомментированные примеры
`mem_limit`, `cpus`, `pids_limit` и `ulimits`; включайте их под свой workload.

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
# Фиксированные credentials для локального интерактивного запуска.
# Значение --auth видно в argv/process listings; не используйте так для services/containers.
exphttp --auth 'admin:<strong-password>'

# Credentials из файла, предпочтительно для services/containers/CI.
# Файл должен содержать ровно одну строку user:password; завершающий newline допустим.
exphttp --auth-file /run/secrets/exphttp_auth

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
from exphttp import ExperimentalHTTPServer, BasicAuthenticator

# Кастомная аутентификация
def check_user(username, password):
    return username == "admin" and password == "secret"

auth = BasicAuthenticator(auth_callback=check_user)
server = ExperimentalHTTPServer(host="0.0.0.0", port=443, tls=True)
server.set_authenticator(auth)
server.start()
```

Используйте `set_authenticator()` вместо прямой записи в
`server.authenticator`: setter одновременно включает/выключает auth
rate-limiter, который защищает Basic Auth от быстрой серии неудачных попыток.

## Область доступа uploads/

Сервер всегда ограничивает пользовательские файловые операции рабочей папкой `uploads/` внутри выбранного `--dir`:

- `GET` — встроенный `index.html`, `/static/...` и файлы из `uploads/`
- `FETCH`, `INFO` — только uploads/
- `POST`, `PUT`, `PATCH`, `NONE`, продвинутая загрузка — запись только в uploads/
- `DELETE`, `SMUGGLE` — работа только с uploads/
- Защита от path traversal (`../`)
- `static/` — доступна только для чтения (JS, CSS, изображения)

## Browser-origin защита мутаций

Браузерные запросы, меняющие состояние (`POST`, `PUT`, `PATCH`, `DELETE`,
`NONE`, `NOTE`, `SMUGGLE` и продвинутая загрузка нестандартным методом),
по умолчанию принимаются только от same-origin UI. Cross-origin браузерные
мутации отклоняются с `403`, даже если браузер уже кэшировал Basic Auth.

Для доверенного внешнего UI укажите точный `--cors-origin`; этот же origin
будет использоваться и для CORS-ответов, и для допуска браузерных мутаций.
Обычные API-клиенты без `Origin` и `Sec-Fetch-Site` продолжают работать как
раньше. `--cors-origin *` оставляет CORS для чтения, но не разрешает
браузерные мутации или WebSocket upgrades с произвольного origin.

## HTML Smuggling

Метод `SMUGGLE` доступен только в `--profile lab` и генерирует временный HTML-артефакт с файлом, встроенным в Base64. При открытии этого same-origin артефакта в браузере файл извлекается из самого HTML и скачивается без повторного запроса к исходному файлу.

### Зачем

- Контролируемая lab-only демонстрация того, как браузер извлекает встроенный файл из временного HTML-артефакта
- Проверка same-origin artifact flow и retention policy без ослабления обычного UI CSP
- Одноразовая выдача: временный HTML-файл удаляется после первого GET/HEAD-запроса

Не используйте `SMUGGLE` как совет по обходу DLP/прокси, массовой доставке или передаче через сторонние каналы. Это лабораторный, operator-owned сценарий для контролируемой проверки и отладки.

### Параметры

| Параметр (query string) | Описание |
|--------------------------|----------|
| `encrypt=1` | Включить XOR-шифрование (пароль генерируется на сервере) |

При шифровании (`encrypt=1`):
- Сервер генерирует случайный 7-символьный пароль (A-Z, 0-9)
- Пароль отображается как CAPTCHA-изображение на странице скачивания
- Пароль возвращается в JSON-ответе, чтобы lab-automation могла проверить артефакт end-to-end
- Пользователь вводит пароль для расшифровки файла в браузере (CryptoJS SHA256 + XOR)

### Пример

Требуется `--profile lab`.

```bash
# Создать HTML Smuggling страницу для файла (без шифрования)
curl -X SMUGGLE http://localhost:8080/uploads/secret.txt
# Ответ: {"url": "/uploads/smuggle_0123abcd4567ef89.html", "file": "secret.txt", "encrypted": false}
# Заголовок: X-Smuggle-URL: /uploads/smuggle_0123abcd4567ef89.html

# С шифрованием
curl -X SMUGGLE "http://localhost:8080/uploads/secret.txt?encrypt=1"
# Ответ: {"url": "/uploads/smuggle_fedcba9876543210.html", "file": "secret.txt", "encrypted": true, "password": "ABC1234"}
# Заголовок: X-Smuggle-URL: /uploads/smuggle_fedcba9876543210.html

# Скачать HTML-страницу (файл удалится автоматически после отдачи)
curl http://localhost:8080/uploads/smuggle_0123abcd4567ef89.html -o smuggle.html
```

### Автоматическая очистка

- Временные HTML-файлы (`smuggle_*.html`) удаляются после первого GET/HEAD-запроса или совпавшего conditional-запроса
- При перезапуске сервера все оставшиеся `smuggle_*.html` в `uploads/` очищаются автоматически
- Перед созданием новой страницы сервер применяет retention policy для временных SMUGGLE HTML по возрасту, количеству файлов и общему размеру; если место освободить нельзя, возвращается JSON `507` без временного URL
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
from exphttp import ExperimentalHTTPServer, xor_encrypt, xor_decrypt

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

### Плагины

Внешние расширения подключаются только явным allowlist через `[plugins]`.
Автозагрузки entry points нет. Минимальный plugin API доступен из
`exphttp.extensions`:

```python
from exphttp.extensions import HandlerContext, PluginMethodSpec, PluginSpec
from exphttp import HTTPRequest, HTTPResponse


def handle_echo(request: HTTPRequest, context: HandlerContext) -> HTTPResponse:
    response = HTTPResponse(200)
    response.set_body(b"ok", "text/plain")
    return response


plugin = PluginSpec(
    name="demo",
    methods=(
        PluginMethodSpec(
            method="ECHO",
            handler=handle_echo,
            mutating=False,
            cors_allowed=True,
            profiles=("workspace", "lab"),
        ),
    ),
)
```

Методы плагинов не могут перезаписывать core HTTP methods без явного
`plugins_override_core`. Capability gating профиля определяет, какие встроенные
методы активны прямо сейчас, но не освобождает их имена для плагина:
`SMUGGLE`, `NOTE` и другие built-in names остаются зарезервированными даже в
`workspace`/`serve`, пока оператор явно не включит override. `PING` возвращает
`plugin_methods` отдельно от core `capabilities`; browser mutation guard
использует флаг `mutating`.

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

# Очистить uploads/ (требуется --profile lab; скрытые служебные файлы сохраняются)
curl -X DELETE "http://localhost:8080/uploads?clear=1"

# Очистить заметки отдельно от uploads/ (требуется --profile lab)
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

# Загрузка (продвинутая; требуется --profile lab)
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

// Продвинутая загрузка текстового payload; требуется --profile lab
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

# Продвинутая загрузка: требуется --profile lab; используйте любой нестандартный метод с payload
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
- **Browser-origin guard** — cross-origin браузерные мутации отклоняются, кроме явно разрешённых точным `--cors-origin`
- **Доступ только к uploads/** — ограничение пользовательских файловых операций
- **Таймауты** — защита от Slowloris (30s заголовки, idle/deadline/rate
  контроль тела запроса и bounded streamed-ответы)
- **Лимиты запросов и диска** — `--max-header-size` для заголовков,
  `--max-size` для тела одного запроса, `--body-memory-budget` для
  aggregate in-flight тел запросов в памяти, опциональные
  `--upload-storage-limit`, `--upload-file-limit` и `--upload-reserve-free`
  для aggregate quota `uploads/`, `--note-storage-limit` и
  `--note-count-limit` для encrypted blobs в `notes/`, отдельный 1 MiB decoded
  limit для Secure Notepad blobs, а также age/count/byte retention для
  временных SMUGGLE HTML и `--max-websocket-connections` для WebSocket
  admission budget
- **Скрытые файлы** — любые path-сегменты с leading dot, включая dotfiles в `uploads/`, недоступны через GET и INFO
- **User content hardening** — загруженные HTML/SVG отдаются как attachment, а ответы получают `X-Content-Type-Options: nosniff`
- **CSP для UI** — встроенный HTML ограничивает scripts до `'self'`; inline
  styles временно разрешены только для текущих UI progress widgets
- **HMAC** — опциональная проверка целостности данных в продвинутой загрузке

### Ограничения XOR-шифрования

XOR-шифрование используется для **обфускации**, а не криптографической защиты:

- Уязвим к частотному анализу
- Повторяющийся ключ легко восстановить
- Нет аутентификации данных

Для реальной защиты рекомендуется использовать AES-GCM или ChaCha20-Poly1305.

## Технические детали

- **Socket timeout**: 5 секунд ожидания первого запроса/keep-alive recv,
  30s headers, 5s body idle, 300s body deadline, optional body min-rate
- **Max headers**: 64 KiB по умолчанию (`--max-header-size`)
- **Chunk size**: 65536 байт (64 KB) для приёма и стриминга файлов
- **Streamed response timeout**: 5s send idle, 300s total transfer deadline
- **Backlog**: 128 соединений
- **HTTP версия**: 1.1
- **Кодировка**: UTF-8
- **Worker threads**: 10 (по умолчанию)
- **Max upload request**: 100 MB (по умолчанию)
- **Body memory budget**: по умолчанию `workers * max upload request`;
  настраивается через `--body-memory-budget`
- **WebSocket limits**: по умолчанию `workers // 2` активных соединений и
  5s incomplete-frame idle timeout; настраивается через
  `--max-websocket-connections` и `--websocket-frame-idle-timeout`
- **Upload storage quota**: unlimited по умолчанию; настраивается через
  `--upload-storage-limit`, `--upload-file-limit`, `--upload-reserve-free`
- **Notepad storage quota**: 256 MB и 1000 заметок по умолчанию; `0`
  отключает соответствующий aggregate limit
- **SMUGGLE temp retention**: 3600 секунд, 32 файла и 128 MB по умолчанию;
  `0` отключает соответствующий retention limit
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

# Локально как в CI (pytest + hypothesis + benchmark + mypy + ruff)
PIP_CONSTRAINT=constraints/ci.txt pip install -e ".[dev,lint,test]"

# Документация сайта
pip install -e ".[docs]"

# Всё вместе
pip install -e ".[all]"
```

Для воспроизводимой установки теми же версиями инструментов, что и в CI,
security workflow и Docker wheel build, используйте общий constraints-файл.
Он также фиксирует `pre-commit`, который входит в `dev` extra:

```bash
PIP_CONSTRAINT=constraints/ci.txt pip install -e ".[dev,lint,test]"
```

`constraints/ci.txt` — единственный коммитимый источник закрепленных версий
для CI, Docker, security workflow, документации и воспроизводимой локальной
установки. Локальный `uv.lock` намеренно игнорируется: если используете uv,
пересобирайте lock из текущих `pyproject.toml` и constraints, но не
коммитьте его.

Поддерживаемая матрица Python — 3.10-3.14. Метаданные пакета ограничены
диапазоном `<3.15`; CI проверяет Python 3.14 в constrained test matrix, а
отдельный readiness job выполняет `pip check`, import smoke, wheel smoke и
`pip-audit` с `constraints/ci.txt`.

В Windows PowerShell задайте constraint как переменную окружения:

```powershell
$env:PIP_CONSTRAINT = "constraints/ci.txt"
pip install -e ".[dev,lint,test]"
Remove-Item Env:PIP_CONSTRAINT
```

Если используете локальные hooks, они закрепляют те же версии `ruff` и
`mypy`, что и CI:

```bash
pre-commit run --all-files
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

Browser smoke является release-gating проверкой в CI. Пакет
`@playwright/cli` закреплен в `.github/workflows/ci.yml` и
`tools/browser_smoke.py`; обновляйте эти pins вместе.

### Release artifacts

Workflow `Release Artifacts` запускается по тегам `v*` и вручную через
`workflow_dispatch`. Для тегов `vX.Y.Z` он проверяет, что
`src.config.__version__ == X.Y.Z`, собирает Python artifacts, публикует пакет
в PyPI через Trusted Publishing/OIDC и публикует image
`ghcr.io/gkumurzhi/exphttp`.

Release lane собирает wheel и sdist из clean checkout, устанавливает wheel в
новый venv вне source tree, проверяет `exphttp --version`, `exphttp --help`,
import paths, static UI assets из самого wheel и browser smoke в режиме
`tools/browser_smoke.py --installed-package`. Если package imports резолвятся
в checkout вместо установленного wheel, smoke падает.

Workflow использует явные permissions: `contents: read`, `packages: write`,
`id-token: write`, `attestations: write`. `pip-audit` сканирует закрепленный
`constraints/ci.txt`, формирует CycloneDX JSON SBOM, а GitHub artifact
attestations подписывают wheel, sdist, dependency SBOM и GHCR image digest.
Container build включает BuildKit `sbom: true` и `provenance: true`.

Rollback для Python-пакета в пределах этого окна выполняется установкой
предыдущей проверенной версии wheel/sdist из release artifacts. Если нужен
rollback старше 90 дней, maintainer должен заранее сохранить проверенный
wheel/sdist вне GitHub Actions artifact retention или повторно собрать его из
подписанного тега. Container rollback выполняется на предыдущий проверенный
GHCR digest, а не на плавающий tag.

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

# Семантическая проверка устаревших docs/API/security claims
python tools/check_stale_docs.py

# Пересборка docs/ из root-canonical файлов
python tools/sync_docs.py --write

# Сборка сайта документации
mkdocs build --strict
```

## Лицензия

MIT
