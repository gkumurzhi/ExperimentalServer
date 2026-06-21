#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-exphttp}"
APP_GROUP="${APP_GROUP:-exphttp}"
APP_HOME="${APP_HOME:-/home/${APP_USER}}"
APP_PREFIX="${APP_PREFIX:-/opt/exphttp}"
APP_STATE="${APP_STATE:-/var/lib/exphttp}"
APP_CONFIG="${APP_CONFIG:-/etc/exphttp}"
APP_PACKAGE="${APP_PACKAGE:-exphttp}"

if [ "$(id -u)" -ne 0 ]; then
  echo "install-systemd.sh must be run as root" >&2
  exit 1
fi

if ! getent group "${APP_GROUP}" >/dev/null; then
  groupadd --system "${APP_GROUP}"
fi

if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd \
    --system \
    --gid "${APP_GROUP}" \
    --home-dir "${APP_HOME}" \
    --create-home \
    --shell /usr/sbin/nologin \
    "${APP_USER}"
fi

install -d -m 0755 "${APP_PREFIX}"
install -d -m 0750 -o "${APP_USER}" -g "${APP_GROUP}" "${APP_STATE}"
install -d -m 0750 -o root -g "${APP_GROUP}" "${APP_CONFIG}"
install -d -m 0750 -o "${APP_USER}" -g "${APP_GROUP}" "${APP_HOME}/.exphttp"

python3 -m venv "${APP_PREFIX}/venv"
"${APP_PREFIX}/venv/bin/python" -m pip install --upgrade pip
"${APP_PREFIX}/venv/bin/python" -m pip install "${APP_PACKAGE}"

if [ ! -f "${APP_CONFIG}/exphttp.ini" ]; then
  install -m 0640 -o root -g "${APP_GROUP}" \
    "$(dirname "$0")/exphttp.ini.example" \
    "${APP_CONFIG}/exphttp.ini"
fi

if [ ! -f "${APP_CONFIG}/exphttp.env" ]; then
  install -m 0640 -o root -g "${APP_GROUP}" \
    "$(dirname "$0")/exphttp.env.example" \
    "${APP_CONFIG}/exphttp.env"
fi

if [ ! -f "${APP_CONFIG}/auth" ]; then
  umask 0177
  password="$("${APP_PREFIX}/venv/bin/python" - <<'PY'
import secrets
print(secrets.token_urlsafe(24))
PY
)"
  printf 'admin:%s\n' "${password}" > "${APP_CONFIG}/auth"
  chown root:"${APP_GROUP}" "${APP_CONFIG}/auth"
  chmod 0640 "${APP_CONFIG}/auth"
fi

install -m 0644 "$(dirname "$0")/exphttp.service" /etc/systemd/system/exphttp.service
systemctl daemon-reload

cat <<EOF
Installed exphttp systemd files.

Review:
  ${APP_CONFIG}/exphttp.ini
  ${APP_CONFIG}/auth

Then run:
  systemctl enable --now exphttp
  journalctl -u exphttp -f
EOF
