# Cluster Review: Refactoring & Code Quality

## Agents Used
- refactoring-specialist
- senior-code-reviewer

## Analysis Scope
- Code duplication analysis
- Complexity hotspot identification
- Type hint assessment
- Naming convention review
- Code organization evaluation
- Linting configuration review

---

## Code Quality Analysis

### Duplication Analysis

#### 1. Path Traversal Validation Pattern (CRITICAL DUPLICATION)

The path traversal check pattern is repeated across multiple files:

**Location 1: `src/handlers/base.py:93-100`**
```python
# Проверяем, что путь находится внутри upload_dir
if not str(file_path).startswith(str(self.upload_dir)):
    return None
```

**Location 2: `src/handlers/info.py:34-35`**
```python
if not str(file_path).startswith(str(self.root_dir)):
    file_path = None
```

**Location 3: `src/http/utils.py:110-117`**
```python
if not str(file_path).startswith(str(sandbox_dir)):
    return None
...
if not str(file_path).startswith(str(base_dir)):
    return None
```

| Duplication | Files | Lines | Impact |
|-------------|-------|-------|--------|
| Path traversal check | 3 files | ~15 lines | HIGH - Security-critical code should be centralized |

**Recommendation**: Extract to a single utility function `is_path_safe(path: Path, base_dir: Path) -> bool`.

#### 2. HTTP Response Helper Pattern

Similar response building patterns appear in multiple handlers:

**Pattern in `handlers/base.py:117-144`**:
```python
def _not_found(self, path: str) -> HTTPResponse:
    response = HTTPResponse(404)
    response.set_body(f"File not found: {path}", "text/plain")
    return response
```

**Pattern in `handlers/opsec.py:55-60`**:
```python
response = HTTPResponse(400)
response.set_body(
    json.dumps({"ok": False, "err": "hmac"}),
    "application/json"
)
return response
```

**Pattern in `handlers/files.py:133-139`**:
```python
response = HTTPResponse(404)
response.set_header("X-Fetch-Status", "file-not-found")
error_msg = f"Cannot fetch: {request.path}"
...
response.set_body(error_msg, "text/plain")
```

| Duplication | Files | Lines | Impact |
|-------------|-------|-------|--------|
| Response building | 4 files | ~40 lines | MEDIUM - Inconsistent error response formats |

#### 3. File Reading Pattern

The pattern of reading a file and setting response body is repeated:

**Pattern 1 (`handlers/files.py:88-95`):**
```python
with open(file_path, "rb") as f:
    content = f.read()
...
response.set_body(content, content_type)
```

**Pattern 2 (`handlers/files.py:143-149`):**
```python
with open(file_path, "rb") as f:
    content = f.read()
content_type, _ = mimetypes.guess_type(str(file_path))
...
response.set_body(content, content_type)
```

**Pattern 3 (`handlers/smuggle.py:52-54`):**
```python
with open(file_path, "rb") as f:
    file_data = f.read()
```

| Duplication | Files | Lines | Impact |
|-------------|-------|-------|--------|
| File read + response | 2 files | ~20 lines | LOW - Context-specific variations justified |

#### 4. Unique Filename Generation Duplication

**Location 1: `src/http/utils.py:122-143` (make_unique_filename)**
**Location 2: `src/handlers/opsec.py:75-81`**

```python
# In opsec.py
if file_path.exists():
    name_parts = safe_filename.rsplit(".", 1)
    if len(name_parts) == 2:
        safe_filename = f"{name_parts[0]}_{secrets.token_hex(4)}.{name_parts[1]}"
    else:
        safe_filename = f"{safe_filename}_{secrets.token_hex(4)}"
    file_path = self.upload_dir / safe_filename
```

| Duplication | Files | Lines | Impact |
|-------------|-------|-------|--------|
| Unique filename logic | 2 files | ~15 lines | MEDIUM - OPSEC uses different uniquifier (hex vs timestamp) |

#### 5. XOR Encryption Duplication (SIGNIFICANT)

There are TWO implementations of XOR encryption:

**Location 1: `src/security/crypto.py:9-29`**
```python
def xor_encrypt(data: bytes, password: str) -> bytes:
    key_bytes = password.encode('utf-8')
    result = bytearray(len(data))
    for i in range(len(data)):
        result[i] = data[i] ^ key_bytes[i % len(key_bytes)]
    return bytes(result)
```

**Location 2: `src/utils/smuggling.py:9-18`**
```python
def xor_encrypt(data: bytes, password: str) -> bytes:
    """XOR шифрование с ключом из SHA256 пароля."""
    key = hashlib.sha256(password.encode('utf-8')).digest()
    key_len = len(key)
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % key_len])
    return bytes(result)
```

| Duplication | Files | Lines | Impact |
|-------------|-------|-------|--------|
| XOR encryption | 2 files | ~25 lines | HIGH - Different algorithms with same function name! |

**CRITICAL**: These two functions have the SAME NAME but DIFFERENT BEHAVIOR:
- `security/crypto.py`: Uses raw password as key
- `utils/smuggling.py`: Uses SHA256 hash of password as key

This is a maintenance hazard and potential security issue.

---

### Complexity Hotspots

| Location | Issue | Complexity | Metrics | Recommendation |
|----------|-------|------------|---------|----------------|
| `server.py:289-354` | `_handle_client` method | HIGH | 65 lines, 4 nesting levels, 8 branches | Extract auth check, error handling, and response sending to separate methods |
| `server.py:36-103` | `__init__` method | HIGH | 67 lines, many responsibilities | Extract initialization logic into separate methods |
| `handlers/files.py:44-106` | `handle_get` method | HIGH | 62 lines, 4 nesting levels | Extract sandbox logic and file serving into helper methods |
| `handlers/info.py:16-93` | `handle_info` method | MEDIUM | 77 lines, complex path logic | Extract path resolution and sandbox logic |
| `handlers/opsec.py:18-99` | `handle_opsec_upload` | MEDIUM | 81 lines, complex JSON parsing | Extract payload parsing and file saving into separate functions |
| `utils/captcha.py:11-104` | `generate_password_captcha` | MEDIUM | 93 lines, procedural | Could split into smaller SVG generation helpers |
| `utils/smuggling.py:95-179` | `_create_html_with_password` | LOW | Single f-string template, acceptable |

#### Detailed Analysis of Top Complexity Hotspots

**1. `server.py:_handle_client` (65 lines)**

Issues:
- Multiple responsibilities: request receiving, auth checking, handler dispatching, error handling
- Deep nesting (try/except with if/else)
- Mixed concerns (logging, response building, socket handling)

```python
def _handle_client(self, client_socket, client_address):
    try:
        data = self._receive_request(client_socket)
        if not data:
            return
        request = HTTPRequest(data)

        # Auth check - could be extracted
        if self.authenticator:
            auth_header = request.headers.get("authorization")
            if not self.authenticator.authenticate(auth_header):
                # 10 lines of response building
                ...

        # Content-length check - could be extracted
        content_length = int(request.headers.get("content-length", 0))
        if content_length > self.max_upload_size:
            # Response building
            ...

        # Handler dispatch - could be simplified
        if self.opsec_mode:
            handler = self._get_opsec_handler(request)
        else:
            handler = self.method_handlers.get(request.method)

        if handler:
            response = handler(request)
        else:
            # More branching
            ...
```

**Suggested Refactoring**:
```python
def _handle_client(self, client_socket, client_address):
    try:
        request = self._parse_request(client_socket)
        if not request:
            return

        response = self._process_request(request, client_address)
        client_socket.sendall(response.build(opsec_mode=self.opsec_mode))
    except Exception as e:
        self._handle_error(client_socket, e)
    finally:
        client_socket.close()

def _process_request(self, request, client_address):
    if error := self._check_auth(request):
        return error
    if error := self._check_content_length(request):
        return error
    return self._dispatch_handler(request, client_address)
```

**2. `handlers/files.py:handle_get` (62 lines)**

Issues:
- Complex sandbox mode branching
- Multiple file path resolution strategies
- Mixing concerns (sandbox check, index.html fallback, content serving)

Cyclomatic complexity estimate: 12 (7 if statements, 5 logical branches)

**3. `handlers/info.py:handle_info` (77 lines)**

Similar pattern to handle_get with duplicated sandbox logic.

---

### Type Hint Assessment

#### Completeness: 95% (Excellent)

| Category | Status | Notes |
|----------|--------|-------|
| Function parameters | Complete | All public functions have type hints |
| Return types | Complete | All functions have return type hints |
| Class attributes | Mostly Complete | Some mixin attributes declared without types in base |
| Generic types | Modern syntax | Uses `X | None` instead of `Optional[X]` |
| Container types | Modern syntax | Uses `dict[str, str]` instead of `Dict[str, str]` |

#### Issues Found

**1. Implicit `Any` in exception handlers**

`server.py:342-352`:
```python
except Exception as e:
    logger.error(f"Ошибка обработки запроса: {e}")
```
The `e` variable is implicitly `Exception` but could be more specific.

**2. Missing return type annotation**

`server.py:386`:
```python
def _get_opsec_handler(self, request: HTTPRequest):  # Missing return type
```

Should be:
```python
def _get_opsec_handler(self, request: HTTPRequest) -> Callable[[HTTPRequest], HTTPResponse] | None:
```

**3. Incomplete TYPE_CHECKING imports**

`handlers/base.py:12-13`:
```python
if TYPE_CHECKING:
    from ..server import ExperimentalHTTPServer
```

The imported type is never used in annotations - this block could be removed.

**4. Mixin attribute declarations without defaults**

`handlers/base.py:52-57`:
```python
class BaseHandler:
    # Атрибуты, которые будут установлены из сервера
    root_dir: Path
    upload_dir: Path
    method_handlers: dict
    sandbox_mode: bool
    opsec_mode: bool
```

These should use `ClassVar` or be properly typed as instance attributes expected from the composition.

**5. Handler return type should use Protocol**

The `method_handlers` dict has type `dict` but should be:
```python
from typing import Protocol

class HandlerProtocol(Protocol):
    def __call__(self, request: HTTPRequest) -> HTTPResponse: ...

method_handlers: dict[str, HandlerProtocol]
```

---

### Naming Review

#### Positive Patterns

| Pattern | Examples | Assessment |
|---------|----------|------------|
| Method naming | `handle_get`, `handle_post`, `handle_opsec_upload` | Consistent, clear |
| Private methods | `_setup_auth`, `_handle_client`, `_receive_request` | Consistent underscore prefix |
| Constants | `HIDDEN_FILES`, `HTTP_STATUS_MESSAGES`, `OPSEC_METHOD_PREFIXES` | UPPER_SNAKE_CASE |
| Classes | `HTTPRequest`, `HTTPResponse`, `BasicAuthenticator` | PascalCase |

#### Issues Found

| Issue | Location | Current | Suggested | Severity |
|-------|----------|---------|-----------|----------|
| Abbreviated name | `http/response.py:57` | `_set_cors_headers` | Good | OK |
| Inconsistent style | `handlers/opsec.py:88-91` | `ok`, `id`, `sz` | `success`, `file_id`, `size` | LOW - intentional for OPSEC |
| Russian comments | Throughout | `# Парсинг...` | English comments | MEDIUM - internationalization |
| Magic number | `handlers/base.py:82` | `8` | `UPLOADS_PREFIX_LEN = 8` | LOW |
| Magic number | `handlers/info.py:26` | `8` | Same constant | LOW |
| Single letter variable | `server.py:149` | `f` | `config_file` | LOW |
| Generic exception | `http/request.py:48` | `except Exception as e` | More specific exceptions | MEDIUM |

#### Naming Consistency Issues

1. **Mixed language in identifiers and comments**:
   - File: `server.py:2` - `"""Основной HTTP-сервер..."""`
   - While Russian comments don't affect functionality, they reduce maintainability for international contributors.

2. **Inconsistent error message style**:
   - Some use English: `"File not found: {path}"`
   - Some use Russian: `"Ошибка обработки запроса"`
   - Log messages mix languages

3. **Naming convention for sandbox parameters**:
   - `for_sandbox: bool` - good
   - `sandbox_mode: bool` - good
   - `sandbox_dir` - good
   - Consistent usage throughout

---

### Code Organization

#### Module Structure Assessment

```
src/
├── __init__.py          # 66 lines - Clean public API export
├── __main__.py          # Entry point
├── cli.py               # 160 lines - Well-structured argument parsing
├── config.py            # 93 lines - Good configuration centralization
├── exceptions.py        # 80 lines - Well-designed exception hierarchy
├── server.py            # 408 lines - LARGEST FILE, needs refactoring
├── handlers/
│   ├── __init__.py      # 38 lines - Clean mixin composition
│   ├── base.py          # 145 lines - Good base class
│   ├── files.py         # 221 lines - Could be split
│   ├── info.py          # 112 lines - Appropriate size
│   ├── opsec.py         # 100 lines - Appropriate size
│   └── smuggle.py       # 82 lines - Appropriate size
├── http/
│   ├── __init__.py      # 24 lines - Clean
│   ├── request.py       # 67 lines - Well-focused
│   ├── response.py      # 83 lines - Well-focused
│   └── utils.py         # 144 lines - Good utilities
├── security/
│   ├── __init__.py      # 51 lines - Clean exports
│   ├── auth.py          # 159 lines - Well-structured
│   ├── crypto.py        # 147 lines - Well-structured
│   └── tls.py           # 164 lines - Well-structured
└── utils/
    ├── __init__.py      # 12 lines - Minimal
    ├── captcha.py       # 115 lines - Appropriate
    └── smuggling.py     # 180 lines - Appropriate
```

#### Function Size Analysis

| File | Largest Function | Lines | Assessment |
|------|------------------|-------|------------|
| `server.py` | `__init__` | 67 | TOO LARGE - Should be <30 lines |
| `server.py` | `_handle_client` | 65 | TOO LARGE - Extract sub-methods |
| `server.py` | `start` | 62 | BORDERLINE - Complex but acceptable |
| `handlers/info.py` | `handle_info` | 77 | TOO LARGE - Extract helpers |
| `handlers/files.py` | `handle_get` | 62 | BORDERLINE - Consider extraction |
| `handlers/files.py` | `handle_none` | 60 | BORDERLINE - Acceptable |
| `utils/captcha.py` | `generate_password_captcha` | 93 | TOO LARGE - Split into helpers |
| `utils/smuggling.py` | `_create_html_with_password` | 84 | Acceptable - mostly template |

#### Single Responsibility Assessment

| Module | Responsibilities | Assessment |
|--------|------------------|------------|
| `server.py` | Socket handling, TLS, Auth, Logging, OPSEC config, Handler dispatch | TOO MANY |
| `handlers/files.py` | GET, POST, OPTIONS, FETCH, NONE, HTML processing | Multiple HTTP methods - acceptable for mixin |
| `config.py` | Config dataclass, Constants | Appropriate |
| `http/request.py` | Request parsing only | Excellent |
| `http/response.py` | Response building only | Excellent |

**Recommendation for `server.py`**:
Extract into:
1. `server.py` - Core server loop and socket handling
2. `server_config.py` - Configuration and setup methods (TLS, Auth, Logging)
3. `request_handler.py` - Request processing logic

---

### Refactoring Opportunities

| Opportunity | Location | Benefit | Risk | Priority |
|-------------|----------|---------|------|----------|
| Extract `is_path_safe()` utility | `handlers/base.py`, `handlers/info.py`, `http/utils.py` | Centralized security, reduced duplication | LOW - pure function | HIGH |
| Consolidate XOR encryption | `security/crypto.py`, `utils/smuggling.py` | Single source of truth, prevent bugs | MEDIUM - behavior change | HIGH |
| Extract `_check_auth()` from `_handle_client` | `server.py:298-309` | Reduced complexity, testability | LOW | MEDIUM |
| Extract `_check_content_length()` from `_handle_client` | `server.py:311-320` | Reduced complexity | LOW | MEDIUM |
| Add `make_json_response()` helper | `handlers/base.py` | Consistency, reduced boilerplate | LOW | MEDIUM |
| Split `__init__` into setup methods | `server.py:36-103` | Readability, testability | MEDIUM - constructor contract | MEDIUM |
| Use `get_safe_path()` from utils | `handlers/base.py:64-110`, `handlers/info.py:23-48` | DRY - function exists but not used! | LOW | HIGH |
| Extract CAPTCHA SVG builders | `utils/captcha.py` | Readability, testability | LOW | LOW |
| Add return type to `_get_opsec_handler` | `server.py:386` | Type safety | NONE | LOW |
| Convert magic numbers to constants | Multiple | Maintainability | NONE | LOW |

#### Detailed Refactoring: Unused `get_safe_path` Function

The utility function `get_safe_path()` in `src/http/utils.py:84-119` is defined but NOT USED anywhere in the codebase. Instead, similar logic is duplicated in:
- `handlers/base.py:_get_file_path()`
- `handlers/info.py:handle_info()`

This is a significant refactoring opportunity - the utility exists but was never integrated.

---

### Linting Configuration Review

#### pyproject.toml Analysis

**Ruff Configuration:**
```toml
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "PTH"]
```

| Rule Set | Description | Assessment |
|----------|-------------|------------|
| `E` | pycodestyle errors | Good |
| `W` | pycodestyle warnings | Good |
| `F` | Pyflakes | Good |
| `I` | isort | Good |
| `B` | flake8-bugbear | Excellent for bug prevention |
| `C4` | flake8-comprehensions | Good |
| `UP` | pyupgrade | Good for modern Python |
| `PTH` | flake8-use-pathlib | Excellent for this codebase |

**Missing Recommended Rules:**

| Rule | Description | Recommendation |
|------|-------------|----------------|
| `S` | flake8-bandit (security) | HIGHLY RECOMMENDED for HTTP server |
| `N` | pep8-naming | Recommended for naming consistency |
| `RUF` | Ruff-specific rules | Recommended |
| `SIM` | flake8-simplify | Recommended for code simplification |
| `PL` | Pylint rules | Optional but useful |
| `PERF` | perflint | Optional for performance |

**Suggested Ruff Configuration:**
```toml
[tool.ruff.lint]
select = [
    "E", "W", "F", "I", "B", "C4", "UP", "PTH",
    "S",    # Security (bandit)
    "N",    # Naming
    "RUF",  # Ruff-specific
    "SIM",  # Simplify
]
ignore = [
    "S101",  # assert usage OK in tests
]
```

**Mypy Configuration:**
```toml
[tool.mypy]
python_version = "3.10"
strict = true
show_error_codes = true
```

| Setting | Value | Assessment |
|---------|-------|------------|
| `strict` | true | Excellent - enables all strict checks |
| `python_version` | "3.10" | Correct, matches project requirements |
| `show_error_codes` | true | Good for debugging |

**Missing Recommended Mypy Settings:**

```toml
[tool.mypy]
python_version = "3.10"
strict = true
show_error_codes = true
# Additional recommended settings:
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
no_implicit_reexport = true
```

---

### Additional Code Quality Observations

#### 1. Exception Handling Quality

**Good Practices Found:**
- Custom exception hierarchy in `exceptions.py`
- Status codes mapped to exceptions
- Specific exceptions for different error types

**Issues Found:**
- `http/request.py:48`: Catches generic `Exception`
- `handlers/opsec.py:46-47`: Silent exception swallowing
- `security/tls.py:162`: Generic exception catch

#### 2. Logging Consistency

**Good:**
- Single logger name `"httpserver"` used throughout
- Consistent format string

**Issues:**
- Mixed log levels for similar events
- Some error conditions not logged
- `server.py:270`: Uses `logger.debug` for SSL errors (should be `warning` in non-OPSEC)

#### 3. Constants Usage

**Well-defined constants in `config.py`:**
- `HIDDEN_FILES`
- `OPSEC_METHOD_PREFIXES`
- `OPSEC_METHOD_SUFFIXES`
- `HTTP_STATUS_MESSAGES`

**Missing constants that should be added:**
- Magic numbers like `8` for `"uploads/"` prefix length
- Buffer sizes: `65536` in `server.py:363`
- Timeout values: `1.0` in multiple places

#### 4. Documentation Quality

| Category | Quality | Notes |
|----------|---------|-------|
| Module docstrings | Good | All modules have docstrings |
| Class docstrings | Good | All classes documented |
| Function docstrings | Mixed | Some functions missing, some excellent |
| Type hints as docs | Good | Type hints serve as documentation |
| Inline comments | Russian | Limits international collaboration |

---

### Recommendations

| Recommendation | Priority | Files Affected | Effort |
|---------------|----------|----------------|--------|
| Add security rules to ruff (`S` selector) | HIGH | pyproject.toml | LOW |
| Consolidate XOR encryption implementations | HIGH | security/crypto.py, utils/smuggling.py | MEDIUM |
| Use existing `get_safe_path()` utility instead of duplicating | HIGH | handlers/base.py, handlers/info.py | MEDIUM |
| Add return type to `_get_opsec_handler` | HIGH | server.py | LOW |
| Extract request processing from `_handle_client` | MEDIUM | server.py | MEDIUM |
| Split `server.py` `__init__` into focused methods | MEDIUM | server.py | MEDIUM |
| Add missing type hint for `method_handlers` | MEDIUM | handlers/base.py | LOW |
| Extract path validation to centralized function | MEDIUM | 3 files | LOW |
| Add constants for magic numbers | LOW | Multiple files | LOW |
| Standardize on English comments/messages | LOW | All files | HIGH |
| Add `N` (naming) and `SIM` (simplify) rules to ruff | LOW | pyproject.toml | LOW |

---

## Summary

### Overall Code Quality Score: 7.5/10

**Strengths:**
1. **Excellent type hint coverage** (~95%) using modern Python 3.10+ syntax
2. **Well-designed module structure** with clear separation of concerns in most areas
3. **Good use of mixins** for composable handler functionality
4. **Clean exception hierarchy** with HTTP status code mapping
5. **Appropriate use of dataclasses** for configuration
6. **Good linting setup** with ruff and strict mypy

**Weaknesses:**
1. **Critical code duplication** in path traversal validation and XOR encryption
2. **Unused utility function** (`get_safe_path`) while duplicating its logic
3. **High complexity** in `server.py` (especially `_handle_client` and `__init__`)
4. **Missing security-focused linting rules** (flake8-bandit)
5. **Mixed language** in comments and error messages
6. **Large functions** exceeding recommended 30-line guideline

### Technical Debt Estimate

| Category | Debt Level | Remediation Effort |
|----------|------------|-------------------|
| Duplication | MEDIUM | 2-4 hours |
| Complexity | MEDIUM | 4-6 hours |
| Type Safety | LOW | 1-2 hours |
| Naming | LOW | 2-3 hours |
| Documentation | MEDIUM | 3-4 hours |
| Linting Config | LOW | 30 minutes |

**Total estimated remediation: 12-20 hours**

### Immediate Action Items

1. **Add `S` (security/bandit) rules to ruff** - Critical for HTTP server security
2. **Rename or consolidate the two different `xor_encrypt` functions** - Different behavior with same name is dangerous
3. **Refactor `_handle_client` to reduce complexity** - Extract auth and content-length checks
4. **Use the existing `get_safe_path` utility** - Remove duplication in handlers

### Long-term Improvements

1. Consider splitting `server.py` into focused modules
2. Standardize all comments and messages to English
3. Add comprehensive function docstrings with examples
4. Consider adding a `ResponseBuilder` class to simplify response creation patterns
