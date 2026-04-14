# syntax=docker/dockerfile:1.7

# -------- build stage --------
FROM python:3.12-slim AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY pyproject.toml ./
COPY src ./src

# Build a wheel; the [crypto] extra is needed for AES-GCM and ECDH features.
RUN pip install --upgrade pip build && \
    python -m build --wheel --outdir /build/dist

# -------- runtime stage --------
FROM python:3.12-slim AS runtime

ARG APP_USER=exphttp
ARG APP_UID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    EXPHTTP_ROOT=/data

# Add a dedicated non-root user.
RUN groupadd --system --gid ${APP_UID} ${APP_USER} && \
    useradd --system --uid ${APP_UID} --gid ${APP_UID} \
            --home-dir /home/${APP_USER} --create-home \
            --shell /usr/sbin/nologin ${APP_USER}

# Install the wheel; include the crypto extra for full feature parity.
COPY --from=build /build/dist/*.whl /tmp/
RUN pip install --upgrade pip && \
    pip install "$(ls /tmp/*.whl)[crypto]" && \
    rm -f /tmp/*.whl

# Prepare a writable data directory.
RUN mkdir -p ${EXPHTTP_ROOT}/uploads && \
    chown -R ${APP_USER}:${APP_USER} ${EXPHTTP_ROOT}

USER ${APP_USER}
WORKDIR ${EXPHTTP_ROOT}

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request as u, sys; \
r = u.Request('http://127.0.0.1:8080/', method='PING'); \
sys.exit(0 if u.urlopen(r, timeout=2).status == 200 else 1)"

ENTRYPOINT ["exphttp"]
CMD ["--host", "0.0.0.0", "--port", "8080", "--root", "/data", "--sandbox"]
