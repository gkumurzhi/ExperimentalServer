<!-- Generated from ../API.md by tools/sync_docs.py. Edit API.md and rerun the sync tool. -->

# API Reference

All responses include standard headers: `Server`, `Date`, `Connection`, and
`X-Content-Type-Options: nosniff` (`close` by default, `keep-alive` when the
server keeps the socket open).
CORS headers are only emitted when CORS is explicitly enabled.
Error responses use JSON format: `{"error": "message", "status": NNN}`.

---

## GET

Serve the bundled web UI, bundled static assets, and user files from `uploads/`.

**Request:**
```
GET /uploads/path/to/file HTTP/1.1
```

`GET /` and `GET /index.html` serve the built-in UI. `GET /static/...` serves
the built-in UI assets. Other file paths are resolved inside `uploads/`;
`/file.txt` and `/uploads/file.txt` both target `<root>/uploads/file.txt`.

**Response:** File contents with appropriate `Content-Type`. Bundled HTML files
include `Content-Security-Policy`; uploaded HTML/SVG files are forced to
download as attachments.

**Status codes:** `200` OK, `404` Not Found

---

## HEAD

Returns the same headers as GET but with no response body. Useful for checking file existence and metadata without transferring content.

**Request:**
```
HEAD /uploads/path/to/file HTTP/1.1
```

**Response:** Same status code and headers as GET (200 or 404), empty body.

**Status codes:** `200` OK, `304` Not Modified (if ETag matches), `404` Not Found

---

## POST / NONE

Upload a file. POST and NONE both invoke the same upload handler.

**Request:**
```
POST /optional-filename HTTP/1.1
X-File-Name: myfile.txt
Content-Length: 1234

<file bytes>
```

The filename is resolved in order: `X-File-Name` header > URL path > auto-generated timestamp name.

**Response (201):**
```json
{
  "success": true,
  "filename": "myfile.txt",
  "size": 1234,
  "size_human": "1.2 KB",
  "path": "/uploads/myfile.txt",
  "uploaded_at": "2025-01-15T10:30:00",
  "content_type": "text/plain"
}
```

**Headers:** `X-Upload-Status`, `X-File-Name`, `X-File-Size`, `X-File-Path`

**Status codes:** `201` Created, `400` No data, `413` Payload too large, `500` Server error

---

## PUT / PATCH

Aliases for POST/NONE (upload). All four methods (POST, PUT, PATCH, NONE) use the same file upload logic.

---

## DELETE

Delete a file from `uploads/`. Only files inside `uploads/` can be deleted.
To clear the upload workspace, use the explicit clear flag; plain
`DELETE /uploads` still rejects directory deletion.

**Request:**
```
DELETE /uploads/filename.txt HTTP/1.1
```

**Response (200):**
```json
{
  "success": true,
  "deleted": "filename.txt",
  "path": "/uploads/filename.txt"
}
```

**Clear uploads request:**
```
DELETE /uploads?clear=1 HTTP/1.1
```

**Clear uploads response (200):**
```json
{
  "success": true,
  "cleared": true,
  "path": "/uploads",
  "deleted_files": 3,
  "deleted_dirs": 1,
  "preserved": [".gitkeep"]
}
```

Hidden service files such as `.gitkeep` are preserved. Current notepad storage
lives in the separate top-level `notes/` directory; `uploads/notes/` is treated
as ordinary upload content.

**Status codes:** `200` OK, `403` Outside uploads/, `404` Not Found, `400` Cannot delete directory

---

## FETCH

Download a file with `Content-Disposition: attachment`.

**Request:**
```
FETCH /uploads/file.txt HTTP/1.1
```

**Response:** File contents with download headers.

**Headers:** `Content-Disposition`, `X-Fetch-Status`, `X-File-Name`, `X-File-Size`, `X-File-Modified`

**Status codes:** `200` OK, `404` Not Found

---

## INFO

Directory listing as JSON. Supports pagination via query parameters. Paths are
always resolved inside `uploads/`; `/` and `/uploads/` both describe the upload
workspace.

**Request:**
```
INFO /uploads/path?offset=0&limit=100 HTTP/1.1
```

**Query parameters:**
- `offset` (default: 0) — Skip first N items
- `limit` (default: 100, max: 1000) — Number of items to return

**Response (200):**
```json
{
  "path": "/uploads",
  "total_items": 42,
  "offset": 0,
  "limit": 100,
  "contents": [
    {
      "name": "file.txt",
      "type": "file",
      "size": 1234,
      "size_human": "1.2 KB",
      "modified": "2025-01-15T10:30:00"
    }
  ]
}
```

**Status codes:** `200` OK, `404` Not Found

---

## PING

Health check endpoint.

**Request:**
```
PING / HTTP/1.1
```

**Response (200):**
```json
{
  "status": "pong",
  "server": "ExperimentalHTTPServer/2.0.0",
  "timestamp": "2025-01-15T10:30:00.123456+00:00",
  "supported_methods": ["GET", "HEAD", "POST", "PUT", "..."],
  "access_scope": "uploads",
  "advanced_upload": false,
  "metrics": {
    "uptime_seconds": 3600.5,
    "total_requests": 150,
    "total_errors": 2,
    "bytes_sent": 524288,
    "status_counts": {
      "200": 148,
      "404": 2
    }
  }
}
```

The response also includes the header `X-Ping-Response: pong`.

---

## SMUGGLE

Create a temporary HTML smuggling page for a file in `uploads/`. The SMUGGLE
request returns JSON with the temporary URL; clients then fetch that URL with
`GET` to receive the generated HTML page.

**Request:**
```
SMUGGLE /uploads/file.txt HTTP/1.1
```

**With encryption:**
```
SMUGGLE /uploads/file.txt?encrypt=1 HTTP/1.1
```

`encrypt=1` stores an XOR-obfuscated payload in the generated HTML page and
shows a server-generated password CAPTCHA on that page.

**Response (200):**
```json
{
  "url": "/uploads/smuggle_0123abcd4567ef89.html",
  "file": "file.txt",
  "encrypted": false
}
```

**Headers:** `Content-Type: application/json`, `X-Smuggle-URL`

`X-Smuggle-URL` contains the same relative path as the JSON `url` field. A
follow-up `GET` to that path returns the one-shot HTML page (`text/html`) with
the file data embedded as base64. Temporary `smuggle_*.html` files are deleted
after they are served by `GET`, `HEAD`, or a matching conditional request; any
leftover temporary pages are also cleaned up when the server starts.

SMUGGLE source files are capped before HTML generation. The effective cap is
the lower of the SMUGGLE source cap (10 MiB by default) and the configured
upload limit.

**Too large response (413):**
```json
{
  "error": "SMUGGLE source too large. Max size: 10.0 MB",
  "status": 413,
  "file_size": 10485761,
  "file_size_human": "10.0 MB",
  "max_size": 10485760,
  "max_size_human": "10.0 MB"
}
```

**Status codes:** `200` OK, `404` File not found, `413` Source too large

---

## NOTE

Secure Notepad with client-side encrypted note blobs. Clients derive an AES-256-GCM key via ECDH and the server stores only opaque encrypted data plus note metadata. This flow requires the `cryptography` package; when the server is installed without `exphttp[crypto]`, NOTE operations fail closed with `501`. Notes are stored in the separate top-level `notes/` directory as `<id>.enc` + `<id>.meta.json` pairs, alongside `uploads/` rather than inside it.

### NOTE /notes/key

Get the server's ECDH public key.

**Request:**
```
NOTE /notes/key HTTP/1.1
```

**Response (200):**
```json
{
  "hasEcdh": true,
  "publicKey": "<base64 of 65-byte uncompressed P-256 point>"
}
```

If the `cryptography` package is not installed, `hasEcdh` is `false` and `publicKey` is absent. In that mode, save/load/list/delete NOTE operations are unavailable and return `501`.

---

### NOTE /notes/exchange

Exchange ECDH keys to establish a session. The client sends its ephemeral P-256 public key; the server returns a short-lived `sessionId` and its own public key. Both sides independently derive the same AES-256-GCM session key via HKDF-SHA256.

**Request:**
```
NOTE /notes/exchange HTTP/1.1
Content-Type: application/json

{"clientPublicKey": "<base64 of 65-byte uncompressed P-256 point>"}
```

**Response (200):**
```json
{
  "sessionId": "<32-char hex>",
  "serverPublicKey": "<base64 of 65-byte uncompressed P-256 point>",
  "sessionTtlSeconds": 3600
}
```

`sessionId` is audit-only server state: if an active session ID is later sent with a save request, the server records that the note write came from a recent ECDH exchange. It is not an authorization token for reads or writes.

**Status codes:** `200` OK, `400` Missing/invalid key, `501` ECDH unavailable

---

### NOTE /notes — list notes

**Request:**
```
NOTE /notes HTTP/1.1
```

**Response (200):**
```json
{
  "notes": [
    {
      "id": "<32-char hex>",
      "title": "My Note",
      "created_at": "2025-01-15T10:30:00+00:00",
      "updated_at": "2025-01-15T10:30:00+00:00",
      "size": 256
    }
  ],
  "count": 1
}
```

---

### NOTE /notes — save note

Send a JSON body to create or update a note. `data` must be a base64-encoded AES-256-GCM ciphertext (encrypted client-side). Include `id` to update an existing note; omit to create a new one. The encrypted blob is the source of truth, so malformed metadata sidecars are ignored or rebuilt as needed.

**Request:**
```
NOTE /notes HTTP/1.1
Content-Type: application/json
X-Session-Id: <sessionId>   (optional, audit-only; ignored when expired)

{
  "title": "My Note",
  "data": "<base64-encoded encrypted blob>",
  "id": "<32-char hex>"   (omit for new note)
}
```

**Response (201 for new, 200 for update):**
```json
{
  "success": true,
  "id": "<32-char hex>",
  "title": "My Note",
  "created_at": "2025-01-15T10:30:00+00:00",
  "updated_at": "2025-01-15T10:30:00+00:00",
  "size": 256
}
```

**Status codes:** `201` Created, `200` Updated, `400` Bad request, `404` Note not found (for update), `501` Secure Notepad unavailable without `exphttp[crypto]`

---

### NOTE /notes/{id} — load note

**Request:**
```
NOTE /notes/a1b2c3d4... HTTP/1.1
```

**Response (200):**
```json
{
  "id": "<32-char hex>",
  "title": "My Note",
  "data": "<base64-encoded encrypted blob>",
  "created_at": "2025-01-15T10:30:00+00:00",
  "updated_at": "2025-01-15T10:30:00+00:00",
  "size": 256
}
```

**Status codes:** `200` OK, `404` Not Found, `501` Secure Notepad unavailable without `exphttp[crypto]`

---

### NOTE /notes/{id}?delete — delete note

**Request:**
```
NOTE /notes/a1b2c3d4...?delete HTTP/1.1
```

**Response (200):**
```json
{
  "success": true,
  "id": "<32-char hex>"
}
```

**Status codes:** `200` OK, `404` Not Found, `501` Secure Notepad unavailable without `exphttp[crypto]`

---

### NOTE /notes?clear=1 — clear all notes

Deletes all user-visible entries from the separate `notes/` directory. Files in
`uploads/` are not touched.

**Request:**
```
NOTE /notes?clear=1 HTTP/1.1
```

**Response (200):**
```json
{
  "success": true,
  "cleared": true,
  "path": "/notes",
  "deleted_files": 4,
  "deleted_dirs": 0,
  "preserved": []
}
```

Hidden files inside `notes/` are preserved.

**Status codes:** `200` OK, `500` Clear failed, `501` Secure Notepad unavailable without `exphttp[crypto]`

---

## WebSocket — /notes/ws

Real-time notepad sync over WebSocket (RFC 6455). The server detects an upgrade request on any path starting with `/notes/ws` and performs the handshake inline, before the normal HTTP handler runs. The connection uses a 60-second idle timeout; the server sends a ping frame when idle to keep the connection alive. When the server is installed without `exphttp[crypto]`, the upgrade is rejected with `501`.

**Upgrade request:**
```
GET /notes/ws HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: <base64-nonce>
Sec-WebSocket-Version: 13
```

**Response:**
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: <computed accept key>
```

All WebSocket messages are UTF-8 JSON text frames. The client sends masked frames (required by RFC 6455); the server sends unmasked frames.

**Client message types:**

| `type` | Fields | Description |
|--------|--------|-------------|
| `save` | `title`, `data`, `noteId?`, `sessionId?` | Save a note (`sessionId` is optional audit-only state) |
| `load` | `id` | Load a note by ID |
| `list` | — | List all notes |
| `delete` | `id` | Delete a note |

**Server response types:**

| `type` | Fields | Description |
|--------|--------|-------------|
| `saved` | `success`, `id`, `title`, ... | Note saved |
| `loaded` | `id`, `title`, `data`, ... | Note loaded |
| `list` | `notes`, `count` | Note list |
| `deleted` | `success`, `id` | Note deleted |
| `error` | `error` | Error message |

---

## OPTIONS

CORS preflight handler. Returns allowed methods.

**Response (204):** No body. `Access-Control-Allow-Methods` header included.

---

## Advanced Upload

Advanced upload is disabled by default. Start the server with
`--advanced-upload` to treat unknown, non-standard HTTP methods carrying
advanced upload data as upload requests. Writes are still limited to `uploads/`.

The advanced upload endpoint accepts encoded payloads via JSON body, HTTP
headers, or query parameters. Common fields are:

- `d` / `data`: base64-encoded payload
- `e`: encryption mode
- `k`: decryption key
- `kb64`: whether `k` is base64-encoded
- `n` / `name`: suggested filename
- `h` / `hmac`: integrity tag

Header transport also supports chunked payload headers `X-D-0`, `X-D-1`, ... for long values.

**JSON body example:**

**Request:**
```
CHECKDATA / HTTP/1.1
Content-Type: application/json

{"d": "SGVsbG8=", "n": "hello.txt"}
```

**Response (200):**
```json
{
  "ok": true,
  "id": "a1b2c3d4e5f67890",
  "sz": 5,
  "transport": "body"
}
```

**Header transport example:**

**Request:**
```
CHECKDATA /filename HTTP/1.1
X-D: <base64-payload>
X-E: xor
X-K: <password>
X-Kb64: 0
X-N: file.bin
X-H: <hmac-sha256-hex>

<optional raw body if not using structured fields>
```

---

## Authentication

When `--auth` is enabled, all requests require HTTP Basic Auth:

```
Authorization: Basic <base64(user:pass)>
```

Failed auth returns `401` with `WWW-Authenticate` header. Rate limiting applies after 5 failures (30s cooldown, `429` response).

---

## Common Headers

| Header | Description |
|--------|-------------|
| `X-Request-Id` | Unique request correlation ID |
| `X-Upload-Status` | Upload result: `success`, `error`, `no-data` |
| `X-Fetch-Status` | Download result: `success`, `file-not-found` |
| `X-File-Name` | Sanitized filename |
| `X-File-Size` | File size in bytes |
| `X-File-Path` | Path to uploaded file |
| `X-Ping-Response` | Ping result (`pong`) |
