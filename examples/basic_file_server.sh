#!/usr/bin/env bash
# Serve the current directory over HTTPS on port 8443 with a random Basic Auth
# password, sandboxed to `uploads/`. Self-signed certificate is generated
# automatically.

set -euo pipefail

ROOT_DIR="${1:-$(pwd)}"
PORT="${PORT:-8443}"

exec exphttp \
  --host 127.0.0.1 \
  --port "${PORT}" \
  --dir "${ROOT_DIR}" \
  --tls \
  --auth random \
  --sandbox \
  --max-size 100
