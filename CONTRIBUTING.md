# Contributing

## Setup

```bash
git clone <repo-url>
cd ExperimentalHTTPServer
pip install -e ".[dev]"
```

## Development Workflow

1. Create a feature branch from `main`
2. Make changes, ensuring all tests pass
3. Submit a pull request

## Running Tests

```bash
pytest                    # all tests
pytest -x -q              # stop on first failure
pytest --cov=src          # with coverage
```

## Linting

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Code Conventions

- Python 3.10+ type annotations (`X | None`, not `Optional[X]`)
- `pathlib.Path` for all file operations
- Logger name: `"httpserver"`
- Log and print messages in English
- All error responses use JSON: `{"error": "...", "status": NNN}`

## Adding a New HTTP Method

1. Create or extend a mixin in `src/handlers/` inheriting `BaseHandler`
2. Add a `handle_methodname(self, request: HTTPRequest) -> HTTPResponse` method
3. Register in `ExperimentalHTTPServer.method_handlers` dict (`src/server.py`)
4. Add to `HandlerMixin` in `src/handlers/__init__.py`
5. Add tests in `tests/test_handlers/`

## Project Structure

```
src/
  server.py          # Main server class
  cli.py             # CLI argument parsing
  config.py          # Constants and configuration
  handlers/          # HTTP method handlers (mixin pattern)
  http/              # Request/response parsing
  security/          # Auth, TLS, crypto (XOR obfuscation)
  utils/             # Captcha, smuggling helpers
tests/               # pytest test suite
```

## Security

- Always validate paths with `Path.relative_to()` (never `startswith()`)
- Block symlinks in file serving
- Use `secrets` module for security-sensitive randomness
- Add CSP headers to HTML responses
