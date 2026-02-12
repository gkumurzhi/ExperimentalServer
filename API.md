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

## POST / NONE

Upload a file. POST delegates to NONE internally.

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

## PUT

Alias for POST/NONE (upload).

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
