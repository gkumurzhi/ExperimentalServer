# Cluster Review: API & Integration

## Agents Used
- api-architect
- integration-specialist

## Analysis Scope
- HTTP method design and semantics
- Request/Response patterns
- CORS configuration
- Content-Type handling
- Query string parsing
- Error response design
- Method registration architecture

## Files Analyzed
| File | Purpose |
|------|---------|
| `src/http/request.py` | HTTPRequest class - request parsing |
| `src/http/response.py` | HTTPResponse class - response building |
| `src/http/utils.py` | Query string parsing, filename sanitization |
| `src/handlers/files.py` | GET, POST, PUT, FETCH, NONE, OPTIONS handlers |
| `src/handlers/info.py` | INFO, PING handlers |
| `src/handlers/opsec.py` | OPSEC encrypted upload handler |
| `src/handlers/smuggle.py` | HTML Smuggling handler |
| `src/handlers/base.py` | Base handler utilities |
| `src/server.py` | Method registration, request routing |
| `src/config.py` | HTTP status codes, constants |

---

## Findings

### API Design Analysis

#### Overall Architecture Assessment

The server implements a mixin-based architecture for HTTP method handlers, which provides good composability and separation of concerns. The design allows for easy addition of new HTTP methods through the handler registration pattern.

**Strengths of the Architecture:**
1. Clean separation between request parsing, response building, and handler logic
2. Mixin pattern enables modular handler composition
3. Centralized method registration in `ExperimentalHTTPServer.method_handlers`
4. Consistent path traversal protection across handlers

**Architectural Concerns:**
1. Custom HTTP methods diverge from REST/HTTP semantics
2. Method names like `NONE`, `FETCH`, `INFO` may conflict with reserved or emerging HTTP methods
3. No versioning strategy for the API

---

### HTTP Method Reference

| Method | Handler | Purpose | HTTP Semantics Compliance |
|--------|---------|---------|---------------------------|
| GET | `handle_get` | Serve files, index.html | RFC 7231 compliant - safe, idempotent |
| POST | `handle_post` | File upload (delegates to NONE) | Non-standard: should echo body, actually uploads |
| PUT | `handle_none` | File upload | RFC 7231 - should replace resource at URI, here uploads to uploads/ |
| OPTIONS | `handle_options` | CORS preflight | RFC 7231 compliant |
| FETCH | `handle_fetch` | Download with Content-Disposition | Non-standard: conflicts with Fetch API naming |
| INFO | `handle_info` | Directory listing (JSON) | Non-standard: similar to PROPFIND (WebDAV) |
| PING | `handle_ping` | Health check | Non-standard: should use GET /health or HEAD |
| NONE | `handle_none` | Binary file upload | Non-standard: unusual method name |
| SMUGGLE | `handle_smuggle` | Generate HTML smuggling page | Non-standard: specialized functionality |
| OPSEC_* | `handle_opsec_upload` | Encrypted upload (random names) | Non-standard: dynamic method names |

---

### Issues Found

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| CORS wildcard origin | `response.py:60` | HIGH | `Access-Control-Allow-Origin: *` allows any origin to make requests, including malicious sites |
| Custom methods leaked in CORS | `response.py:67-70` | MEDIUM | Non-OPSEC mode exposes custom method names in `Access-Control-Allow-Methods` header |
| POST semantic violation | `files.py:108-110` | MEDIUM | POST delegates to NONE (upload) instead of echoing body as documented |
| PUT semantic violation | `server.py:96` | MEDIUM | PUT should replace resource at path, not upload to `uploads/` directory |
| Sensitive path in PING response | `info.py:104` | HIGH | `root_directory` path is exposed in PING response, reveals server internals |
| Method names in PING | `info.py:103` | MEDIUM | `supported_methods` exposes all registered methods including custom ones |
| Error message information disclosure | `files.py:137` | LOW | Sandbox mode error reveals "sandbox mode: only uploads/ accessible" |
| No Content-Type validation | `files.py:161-210` | MEDIUM | File uploads accept any content without validation |
| Missing X-Content-Type-Options | `response.py` | MEDIUM | No `X-Content-Type-Options: nosniff` header to prevent MIME sniffing |
| Exception details in error response | `server.py:348` | HIGH | Full exception message returned to client: `Internal Server Error: {e}` |
| Silent exception swallowing | `request.py:48-49` | MEDIUM | Request parsing errors logged but continue with empty/partial request |
| Query string URL decoding missing | `utils.py:27` | LOW | Query parameter values not URL-decoded (only path is decoded) |
| Content-Length integer conversion | `request.py:54` | MEDIUM | No validation before `int()` conversion, may raise ValueError |
| Header parsing edge case | `request.py:44` | LOW | Only splits on `: ` (colon-space), fails on headers with just `:` |

---

### Detailed Analysis

#### 1. Request Parsing (`src/http/request.py`)

**What It Does Well:**
- Case-insensitive header storage (line 46)
- URL decoding of path (line 39)
- Clean separation of headers and body parsing

**Issues:**

```python
# Line 54: No validation before int() conversion
def content_length(self) -> int:
    return int(self.headers.get("content-length", 0))
```
If Content-Length contains invalid data (e.g., "abc"), this raises `ValueError`.

```python
# Line 44: Header parsing only handles ": " (colon-space)
if ": " in line:
    key, value = line.split(": ", 1)
```
Headers with no space after colon (rare but valid) are silently ignored.

```python
# Lines 48-49: Exception swallowing
except Exception as e:
    logger.error(f"Ошибка парсинга запроса: {e}")
```
Broad exception catch allows malformed requests to continue processing with partial data.

#### 2. Response Building (`src/http/response.py`)

**What It Does Well:**
- Consistent envelope pattern
- OPSEC mode server masquerading (nginx headers)
- Proper Date header formatting with UTC timezone

**Issues:**

```python
# Line 60: CORS wildcard
self.set_header("Access-Control-Allow-Origin", "*")
```
Security risk: Allows cross-origin requests from any domain, enabling CSRF-like attacks.

```python
# Lines 67-70: Method exposure in CORS
self.set_header(
    "Access-Control-Allow-Methods",
    "GET, POST, PUT, FETCH, INFO, PING, NONE, OPTIONS"
)
```
Reveals custom method names to any client via CORS preflight.

**Missing Security Headers:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` (or SAMEORIGIN)
- `Cache-Control` for sensitive responses

#### 3. CORS Handling Analysis

The CORS implementation has several concerns:

| Aspect | Current Implementation | Recommendation |
|--------|----------------------|----------------|
| Origin | `*` (wildcard) | Validate against whitelist or reflect Origin header |
| Methods | All custom methods exposed | Only expose standard methods or require auth |
| Headers | `Content-Type, X-File-Name` | Appropriate for file operations |
| Expose-Headers | Custom headers exposed | Acceptable for debugging |
| Credentials | Not set | `Access-Control-Allow-Credentials` missing |

**OPSEC Mode Improvement:**
The code correctly hides custom methods in OPSEC mode (lines 63-65), but still uses wildcard origin.

#### 4. Content-Type Detection

```python
# files.py:85-86
content_type, _ = mimetypes.guess_type(str(file_path))
content_type = content_type or "application/octet-stream"
```

**Analysis:**
- Uses Python's `mimetypes` module for detection
- Falls back to `application/octet-stream` for unknown types
- No `X-Content-Type-Options: nosniff` header

**Risk:** Without `nosniff`, browsers may perform MIME sniffing on content, potentially executing malicious JavaScript if an attacker uploads a file with misleading content.

#### 5. Query String Parsing (`src/http/utils.py`)

```python
# Lines 25-30
for param in query.split("&"):
    if "=" in param:
        key, value = param.split("=", 1)
        params[key] = value
    else:
        params[param] = ""
```

**Issues:**
1. Values are not URL-decoded (should use `urllib.parse.unquote`)
2. No handling for `+` as space
3. No limit on number of parameters (potential DoS)
4. Duplicate keys overwrite silently

#### 6. Error Response Design

**Current Pattern:**
```python
# files.py error response example
response.set_body(json.dumps({
    "success": False,
    "error": str(e)
}, indent=2), "application/json")
```

**Issues:**
1. Exception messages may contain sensitive information
2. No consistent error code scheme
3. No request ID for debugging
4. No documentation URL

**Recommended Pattern:**
```json
{
  "error": {
    "code": "UPLOAD_FAILED",
    "message": "File upload failed",
    "request_id": "req_abc123"
  }
}
```

#### 7. Method Handler Registration

```python
# server.py:93-103
self.method_handlers = {
    "GET": self.handle_get,
    "POST": self.handle_post,
    "PUT": self.handle_none,  # PUT тоже загружает файлы
    "OPTIONS": self.handle_options,
    "FETCH": self.handle_fetch,
    "INFO": self.handle_info,
    "PING": self.handle_ping,
    "NONE": self.handle_none,
    "SMUGGLE": self.handle_smuggle,
}
```

**Observations:**
- Clean dictionary-based registration
- Easy to extend with new methods
- PUT and POST both delegate to file upload (semantic confusion)
- No HEAD method implementation (should return GET response without body)

---

### Strengths

1. **Path Traversal Protection**
   - Consistent use of `.resolve()` and `startswith()` checks
   - Centralized in `_get_file_path()` and `get_safe_path()` utilities

2. **Mixin Architecture**
   - Clean separation of handler concerns
   - Easy to add new HTTP methods
   - Shared base functionality in `BaseHandler`

3. **OPSEC Mode Design**
   - Dynamic method name generation
   - Server header masquerading (nginx)
   - Reduced information disclosure

4. **Content-Disposition Headers**
   - FETCH method properly sets `attachment` disposition
   - Filename included in header

5. **JSON Response Consistency**
   - Most handlers return structured JSON responses
   - Human-readable formatting with `indent=2`

6. **Sandbox Mode**
   - Restricts file access to uploads directory
   - Applied across multiple handlers

7. **Filename Sanitization**
   - `sanitize_filename()` removes dangerous characters
   - Unicode (Cyrillic) support with explicit allowlist

---

### Recommendations

| Recommendation | Files to Change | Implementation | Risk |
|---------------|-----------------|----------------|------|
| Replace CORS wildcard with origin validation | `response.py` | Check Origin header against whitelist, reflect valid origins | LOW |
| Add X-Content-Type-Options header | `response.py` | Add `nosniff` in `build()` method | LOW |
| Remove sensitive data from PING | `info.py` | Remove `root_directory`, limit `supported_methods` | LOW |
| Add HEAD method handler | `server.py`, `handlers/files.py` | Create handler returning GET headers without body | LOW |
| Implement proper error envelope | All handlers | Create `ErrorResponse` class with code, message, request_id | MEDIUM |
| Add Content-Length validation | `request.py` | Try/except around `int()` conversion | LOW |
| URL-decode query parameters | `utils.py` | Add `unquote()` call on values | LOW |
| Add rate limiting headers | `response.py` | Track request counts, add X-RateLimit-* headers | MEDIUM |
| Validate Content-Type on upload | `files.py` | Whitelist allowed MIME types or check magic bytes | MEDIUM |
| Reduce exception info disclosure | `server.py` | Log full error, return generic message | LOW |
| Add X-Frame-Options header | `response.py` | Add `DENY` or `SAMEORIGIN` value | LOW |
| Add Cache-Control for dynamic content | `response.py` | Set `no-store` for PING, INFO responses | LOW |

---

### API Design Recommendations for Custom Methods

#### Method Naming Concerns

| Current Method | Issue | Alternative |
|---------------|-------|-------------|
| NONE | Confusing name, conflicts with null concept | UPLOAD, STORE |
| FETCH | Conflicts with browser Fetch API naming | DOWNLOAD, RETRIEVE |
| INFO | Generic, could conflict with future HTTP specs | STAT, LIST, DESCRIBE |
| PING | Should be standard health check | Use `GET /health` endpoint instead |
| SMUGGLE | Specialized, acceptable | Could use query param on existing method |

#### Recommended Endpoint Design (REST Alternative)

If refactoring to REST semantics:

| Current | REST Alternative |
|---------|-----------------|
| `NONE /filename` | `POST /files` with multipart |
| `FETCH /path` | `GET /files/{path}?download=true` |
| `INFO /path` | `GET /files/{path}?metadata=true` |
| `PING /` | `GET /health` |
| `SMUGGLE /path` | `GET /files/{path}?format=smuggle` |

---

### Integration Considerations

#### Client SDK Compatibility

Custom HTTP methods require special handling in clients:

```javascript
// JavaScript - needs XMLHttpRequest or fetch with method override
fetch('/path', { method: 'FETCH' })  // May be rejected by some browsers/proxies

// Python requests
requests.request('FETCH', url)  // Works but unusual

// curl
curl -X FETCH http://host/path  // Works
```

**Recommendation:** Document client compatibility and provide example code for each major language.

#### Proxy Compatibility

Many proxies and CDNs may block or not forward custom HTTP methods:
- Cloudflare: May block unknown methods
- nginx: Requires explicit configuration
- AWS ALB: Has method whitelist

**OPSEC Mode Consideration:** Dynamic method names will definitely fail through standard proxies.

---

## Summary

### Overall API Design Assessment

The ExperimentalHTTPServer implements a functional but unconventional HTTP API. The mixin-based architecture is well-designed for extensibility, and security features like path traversal protection are implemented consistently.

**Key Concerns:**

1. **Security (HIGH Priority)**
   - CORS wildcard origin allows any domain to access the server
   - Sensitive server paths exposed in PING response
   - Exception details leaked in error responses
   - Missing security headers (X-Content-Type-Options, X-Frame-Options)

2. **HTTP Semantics (MEDIUM Priority)**
   - POST and PUT methods don't follow RFC 7231 semantics
   - Custom method names may conflict with future HTTP specifications
   - No HEAD method implementation

3. **Error Handling (MEDIUM Priority)**
   - Inconsistent error envelope format
   - No request IDs for debugging
   - Silent exception swallowing in request parsing

4. **Integration (LOW Priority)**
   - Custom methods reduce client/proxy compatibility
   - No versioning strategy
   - Query parameter values not URL-decoded

### Risk Summary

| Category | Risk Level | Remediation Effort |
|----------|------------|-------------------|
| CORS Configuration | HIGH | LOW (simple header changes) |
| Information Disclosure | HIGH | LOW (remove/mask sensitive data) |
| HTTP Semantics | MEDIUM | MEDIUM (requires API redesign) |
| Error Handling | MEDIUM | MEDIUM (create error framework) |
| Security Headers | MEDIUM | LOW (add headers in response) |
| Request Parsing | LOW | LOW (add validation) |

### Recommended Action Items (Priority Order)

1. **Immediate:** Fix CORS wildcard, add security headers
2. **Immediate:** Remove `root_directory` from PING response
3. **Immediate:** Sanitize exception messages before returning to client
4. **Short-term:** Implement consistent error envelope with error codes
5. **Short-term:** Add Content-Length validation in request parsing
6. **Medium-term:** Consider REST-compliant endpoint alternatives
7. **Medium-term:** Add rate limiting infrastructure
8. **Long-term:** API versioning strategy

---

*Review completed: 2026-01-23*
*Reviewers: api-architect, integration-specialist*
