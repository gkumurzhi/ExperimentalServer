# API Reference

All responses include standard headers: `Server`, `Date`, `Connection: close`, CORS headers.
Error responses use JSON format: `{"error": "message", "status": NNN}`.

---

## GET

Serve files from the root directory (or `uploads/` in sandbox mode).

**Request:**
```
GET /path/to/file HTTP/1.1
```

**Response:** File contents with appropriate `Content-Type`. HTML files include `Content-Security-Policy` header.

**Status codes:** `200` OK, `404` Not Found

---

## HEAD

Returns the same headers as GET but with no response body. Useful for checking file existence and metadata without transferring content.

**Request:**
```
HEAD /path/to/file HTTP/1.1
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

Delete a file from `uploads/`. Always sandbox-restricted — only files inside `uploads/` can be deleted.

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

Directory listing as JSON. Supports pagination via query parameters.

**Request:**
```
INFO /path?offset=0&limit=100 HTTP/1.1
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
  "timestamp": "2025-01-15T10:30:00.123456",
  "uptime_seconds": 3600.5,
  "version": "2.0.0",
  "server_time": "2025-01-15T10:30:00",
  "methods": ["GET", "POST", "PUT", ...],
  "features": {
    "tls": false,
    "auth": false,
    "sandbox": false,
    "opsec": false
  },
  "total_requests": 150,
  "total_bytes_sent": 524288,
  "error_count": 2
}
```

---

## SMUGGLE

Generate an HTML smuggling page for a file. The HTML page contains the file data embedded as base64, downloadable without additional server requests.

**Request:**
```
SMUGGLE /uploads/file.txt HTTP/1.1
```

**With encryption:**
```
SMUGGLE /uploads/file.txt?encrypt=1 HTTP/1.1
```

**Response:** HTML page (`text/html`) with embedded file data.

**Status codes:** `200` OK, `404` File not found, `400` Bad request

---

## NOTE

Secure Notepad with end-to-end AES-256-GCM encryption. The server stores opaque encrypted blobs — plaintext is never visible server-side. ECDH P-256 key exchange is used for automatic session key negotiation (requires the `cryptography` package). Notes are stored in `uploads/notes/` as `<id>.enc` + `<id>.meta.json` pairs.

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

If the `cryptography` package is not installed, `hasEcdh` is `false` and `publicKey` is absent.

---

### NOTE /notes/exchange

Exchange ECDH keys to establish a session. The client sends its ephemeral P-256 public key; the server returns a `sessionId` and its own public key. Both sides independently derive the same AES-256-GCM session key via HKDF-SHA256.

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
  "serverPublicKey": "<base64 of 65-byte uncompressed P-256 point>"
}
```

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

Send a JSON body to create or update a note. `data` must be a base64-encoded AES-256-GCM ciphertext (encrypted client-side). Include `id` to update an existing note; omit to create a new one.

**Request:**
```
NOTE /notes HTTP/1.1
Content-Type: application/json
X-Session-Id: <sessionId>   (optional, for audit trail)

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

**Status codes:** `201` Created, `200` Updated, `400` Bad request, `404` Note not found (for update)

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

**Status codes:** `200` OK, `404` Not Found

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

**Status codes:** `200` OK, `404` Not Found

---

## WebSocket — /notes/ws

Real-time notepad sync over WebSocket (RFC 6455). The server detects an upgrade request on any path starting with `/notes/ws` and performs the handshake inline, before the normal HTTP handler runs. The connection uses a 60-second idle timeout; the server sends a ping frame when idle to keep the connection alive.

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
| `save` | `title`, `data`, `noteId?`, `sessionId?` | Save a note |
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

## OPSEC Mode

When `--opsec` is enabled, standard custom methods (FETCH, INFO, PING, NONE, SMUGGLE) are replaced with randomized method names. The mapping is saved to `.opsec_config.json` in the root directory.

The server masquerades as nginx and does not expose custom method names in CORS or error responses.

OPSEC-specific upload endpoint accepts XOR-obfuscated data with HMAC integrity verification:

**Request:**
```
<RANDOM_METHOD> /filename HTTP/1.1
X-Enc-Key: <password>
X-HMAC: <hmac-sha256-hex>

<XOR-obfuscated bytes>
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
| `X-Request-Id` | Unique request correlation ID (not in OPSEC mode) |
| `X-Upload-Status` | Upload result: `success`, `error`, `no-data` |
| `X-Fetch-Status` | Download result: `success`, `file-not-found` |
| `X-File-Name` | Sanitized filename |
| `X-File-Size` | File size in bytes |
| `X-File-Path` | Path to uploaded file |
| `X-Ping-Response` | Ping result (`pong`) |
