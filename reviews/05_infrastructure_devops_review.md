# Cluster Review: Infrastructure & DevOps

## Agents Used
- docker-containerization-expert
- devops-deployer
- automation-architect
- workflow-orchestrator

## Analysis Scope
- Current infrastructure state assessment
- Missing infrastructure components identification
- Container strategy recommendations
- CI/CD pipeline design
- Production deployment considerations

---

## Current State

### Package Configuration (pyproject.toml)

**Strengths:**
- Well-structured modern `pyproject.toml` using PEP 621 format
- Dynamic versioning from `src.__version__` (currently 2.0.0)
- Clear entry point: `exphttp = "src.cli:main"`
- Separated optional dependencies: `dev`, `lint`, `all`
- Comprehensive tool configuration for pytest, coverage, ruff, mypy
- Proper Python version constraints (>=3.10)
- Good classifier metadata for PyPI

**Observations:**
| Aspect | Status | Notes |
|--------|--------|-------|
| Build system | setuptools 75.0+ | Modern, appropriate choice |
| Entry points | Defined | CLI accessible via `exphttp` command |
| Type hints | Enabled | `py.typed` marker included |
| Dev dependencies | pytest, pytest-cov | Adequate for testing |
| Lint dependencies | ruff, mypy | Modern linting stack |
| Version management | Dynamic | Reads from `src.__version__` |

### CLI Entry Point (src/cli.py)

**Strengths:**
- Clean argument parsing with `argparse`
- Comprehensive CLI options for all server features
- Proper exit codes (0 for success, 1 for errors)
- Graceful KeyboardInterrupt handling

**Container-Relevant CLI Options:**
```
-H, --host      Host binding (default: 127.0.0.1)
-p, --port      Port (default: 8080)
-d, --dir       Root directory
-m, --max-size  Max upload size in MB
-w, --workers   Thread pool workers
--tls           Enable HTTPS
--cert/--key    TLS certificate paths
--auth          Basic authentication
--opsec         OPSEC mode
--sandbox       Sandbox mode
```

### Runtime Dependencies

The application has **zero external runtime dependencies** - it uses only Python standard library. This is excellent for containerization as it:
- Eliminates dependency version conflicts
- Reduces attack surface
- Simplifies image builds
- Minimizes image size

**System Dependencies:**
- Python 3.10+ (required)
- OpenSSL binary (optional, for TLS self-signed cert generation)

---

## Missing Components

| Component | Priority | Current State | Recommendation |
|-----------|----------|---------------|----------------|
| Dockerfile | **CRITICAL** | Missing | Multi-stage build with security hardening |
| .dockerignore | **HIGH** | Missing | Exclude dev artifacts, tests, IDE files |
| docker-compose.yml | **MEDIUM** | Missing | For local development and testing |
| GitHub Actions CI | **CRITICAL** | Missing | Automated testing, linting, type checking |
| GitHub Actions Release | **HIGH** | Missing | Automated PyPI publishing |
| .gitignore (root) | **HIGH** | Missing (only in .idea/) | Exclude build artifacts, venv, caches |
| Makefile | **LOW** | Missing | Developer convenience commands |
| Health check endpoint | **MEDIUM** | Exists (PING) | Already implemented via PING method |

---

## Recommendations

### 1. Dockerfile Template

A production-ready multi-stage Dockerfile optimized for this zero-dependency Python server:

```dockerfile
# =============================================================================
# ExperimentalHTTPServer Dockerfile
# Multi-stage build for minimal, secure production image
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install package and verify
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Prevent Python from writing bytecode and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Copy only what's needed for installation
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Create virtual environment and install package
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir .

# Verify installation
RUN /opt/venv/bin/exphttp --version

# -----------------------------------------------------------------------------
# Stage 2: Test runner (optional, for CI)
# -----------------------------------------------------------------------------
FROM builder AS tester

# Install test dependencies
RUN /opt/venv/bin/pip install --no-cache-dir ".[dev,lint]"

# Copy test files
COPY tests/ ./tests/
COPY tools/ ./tools/

# Run tests
RUN /opt/venv/bin/pytest tests/ -v

# -----------------------------------------------------------------------------
# Stage 3: Production runtime
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Labels for container metadata
LABEL org.opencontainers.image.title="ExperimentalHTTPServer" \
      org.opencontainers.image.description="Feature-rich HTTP server with custom methods, TLS, and OPSEC mode" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.source="https://github.com/OWNER/ExperimentalHTTPServer" \
      org.opencontainers.image.licenses="MIT"

# Security: Run as non-root user
RUN groupadd --gid 1000 httpserver && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home httpserver

# Install OpenSSL for TLS certificate generation (optional feature)
RUN apt-get update && \
    apt-get install --no-install-recommends -y openssl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create uploads directory with proper permissions
WORKDIR /app
RUN mkdir -p /app/uploads && chown -R httpserver:httpserver /app

# Switch to non-root user
USER httpserver

# Expose default HTTP port
EXPOSE 8080

# Health check using the PING method
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1', 8080)); s.send(b'PING / HTTP/1.1\r\nHost: localhost\r\n\r\n'); r=s.recv(100); s.close(); exit(0 if b'PONG' in r else 1)" || exit 1

# Default command - bind to all interfaces for container networking
ENTRYPOINT ["exphttp"]
CMD ["--host", "0.0.0.0", "--port", "8080", "--sandbox"]
```

**Key Security Features:**
- Non-root user execution
- Minimal base image (python:slim)
- No unnecessary packages
- Read-only considerations with sandbox mode default
- Health check for orchestration compatibility

### 2. .dockerignore Template

```dockerignore
# Git
.git
.gitignore

# IDE
.idea/
.vscode/
*.swp
*.swo

# Python artifacts
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
.venv/
ENV/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Type checking
.mypy_cache/

# Documentation (not needed in runtime image)
docs/
*.md
!README.md

# Development files
CLAUDE.md
agents/
reviews/
Makefile

# Temporary files
*.log
*.tmp
.opsec_config.json

# OS files
.DS_Store
Thumbs.db
```

### 3. docker-compose.yml for Development

```yaml
# docker-compose.yml
# Development and testing environment for ExperimentalHTTPServer

services:
  # Production-like server
  httpserver:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    container_name: exphttp-server
    ports:
      - "8080:8080"
    volumes:
      # Persist uploads between restarts
      - uploads:/app/uploads
    environment:
      - PYTHONUNBUFFERED=1
    command: ["--host", "0.0.0.0", "--port", "8080", "--sandbox"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.connect(('127.0.0.1', 8080)); s.close()"]
      interval: 30s
      timeout: 5s
      retries: 3

  # HTTPS variant with self-signed certificate
  httpserver-tls:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    container_name: exphttp-server-tls
    ports:
      - "8443:8443"
    volumes:
      - uploads-tls:/app/uploads
      - certs:/app/certs
    command: ["--host", "0.0.0.0", "--port", "8443", "--tls", "--sandbox"]
    restart: unless-stopped
    profiles:
      - tls

  # Server with authentication
  httpserver-auth:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    container_name: exphttp-server-auth
    ports:
      - "8081:8080"
    volumes:
      - uploads-auth:/app/uploads
    environment:
      - EXPHTTP_AUTH=admin:changeme
    command: ["--host", "0.0.0.0", "--port", "8080", "--auth", "admin:changeme", "--sandbox"]
    restart: unless-stopped
    profiles:
      - auth

  # Test runner
  test:
    build:
      context: .
      dockerfile: Dockerfile
      target: tester
    container_name: exphttp-test
    profiles:
      - test

volumes:
  uploads:
  uploads-tls:
  uploads-auth:
  certs:
```

**Usage:**
```bash
# Start basic server
docker compose up httpserver

# Start with TLS
docker compose --profile tls up httpserver-tls

# Run tests in container
docker compose --profile test run --rm test
```

### 4. GitHub Actions CI/CD Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.12"

jobs:
  # ---------------------------------------------------------------------------
  # Linting and Type Checking
  # ---------------------------------------------------------------------------
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[lint]"

      - name: Run Ruff linter
        run: ruff check src/ tests/

      - name: Run Ruff formatter check
        run: ruff format --check src/ tests/

      - name: Run MyPy type checker
        run: mypy src/

  # ---------------------------------------------------------------------------
  # Testing across Python versions
  # ---------------------------------------------------------------------------
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml --cov-report=term-missing

      - name: Upload coverage to Codecov
        if: matrix.python-version == '3.12'
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

  # ---------------------------------------------------------------------------
  # Docker Build Test
  # ---------------------------------------------------------------------------
  docker:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: exphttp:test
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Test Docker image
        run: |
          docker run --rm exphttp:test --version
          docker run -d --name test-server -p 8080:8080 exphttp:test
          sleep 3
          curl -s http://localhost:8080/ || true
          docker logs test-server
          docker stop test-server

  # ---------------------------------------------------------------------------
  # Security Scanning
  # ---------------------------------------------------------------------------
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: docker
    steps:
      - uses: actions/checkout@v4

      - name: Build image for scanning
        run: docker build -t exphttp:scan .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'exphttp:scan'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
```

### 5. GitHub Actions Release Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ---------------------------------------------------------------------------
  # Build and publish to PyPI
  # ---------------------------------------------------------------------------
  pypi:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For trusted publishing

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # Uses OIDC trusted publishing - configure in PyPI project settings

  # ---------------------------------------------------------------------------
  # Build and publish Docker image
  # ---------------------------------------------------------------------------
  docker:
    name: Publish Docker Image
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Extract version from tag
        id: version
        run: echo "version=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=raw,value=latest

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ---------------------------------------------------------------------------
  # Create GitHub Release
  # ---------------------------------------------------------------------------
  release:
    name: Create GitHub Release
    runs-on: ubuntu-latest
    needs: [pypi, docker]
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
          draft: false
```

### 6. Root .gitignore

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
.venv/
ENV/
env/
.python-version

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
pytest_debug.log

# Type checkers
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
.pytype/

# Ruff
.ruff_cache/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project-specific
.opsec_config.json
*.pem
*.crt
*.key
uploads/*
!uploads/.gitkeep

# Logs
*.log

# Temporary files
*.tmp
*.temp
```

---

## Deployment Architecture Recommendations

### Option 1: Single Container Deployment (Simple)

For small-scale deployments or development environments:

```
                    +------------------+
                    |   Load Balancer  |
                    |   (nginx/caddy)  |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Docker Container |
                    |    exphttp:2.0    |
                    |   Port 8080       |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Volume: uploads  |
                    +------------------+
```

**Deployment Command:**
```bash
docker run -d \
  --name exphttp \
  --restart unless-stopped \
  -p 8080:8080 \
  -v exphttp-uploads:/app/uploads \
  --read-only \
  --tmpfs /tmp \
  --security-opt no-new-privileges:true \
  ghcr.io/owner/exphttp:2.0 \
  --host 0.0.0.0 --port 8080 --sandbox
```

### Option 2: Kubernetes Deployment (Production)

For scalable, production-grade deployments:

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: exphttp
  labels:
    app: exphttp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: exphttp
  template:
    metadata:
      labels:
        app: exphttp
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: exphttp
          image: ghcr.io/owner/exphttp:2.0
          ports:
            - containerPort: 8080
          args:
            - "--host"
            - "0.0.0.0"
            - "--port"
            - "8080"
            - "--sandbox"
          resources:
            requests:
              memory: "64Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          volumeMounts:
            - name: uploads
              mountPath: /app/uploads
            - name: tmp
              mountPath: /tmp
          livenessProbe:
            tcpSocket:
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            tcpSocket:
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: uploads
          persistentVolumeClaim:
            claimName: exphttp-uploads
        - name: tmp
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: exphttp
spec:
  selector:
    app: exphttp
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: exphttp
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - files.example.com
      secretName: exphttp-tls
  rules:
    - host: files.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: exphttp
                port:
                  number: 80
```

### Infrastructure Requirements Summary

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| CPU | 0.1 core | 0.5 core | Per container instance |
| Memory | 64 MB | 256 MB | Depends on file sizes |
| Storage | 1 GB | 10+ GB | For uploads volume |
| Python | 3.10 | 3.12+ | Runtime requirement |
| OpenSSL | Optional | Installed | For TLS self-signed certs |

---

## Security Considerations for Production

### Container Hardening Checklist

- [x] Non-root user execution (UID 1000)
- [x] Minimal base image (python:slim)
- [x] No unnecessary packages installed
- [x] Health checks defined
- [ ] **Recommended:** Read-only root filesystem (`--read-only`)
- [ ] **Recommended:** No new privileges (`--security-opt no-new-privileges:true`)
- [ ] **Recommended:** Drop all capabilities (`--cap-drop ALL`)
- [ ] **Recommended:** Use secrets management for auth credentials

### Network Security

```bash
# Production deployment with network restrictions
docker run -d \
  --name exphttp \
  --network backend \
  --ip 172.20.0.10 \
  -p 127.0.0.1:8080:8080 \  # Bind to localhost only, use reverse proxy
  exphttp:2.0
```

### TLS Recommendations

For production, avoid self-signed certificates. Instead:
1. Use a reverse proxy (nginx, Caddy, Traefik) with Let's Encrypt
2. Mount pre-generated certificates as secrets
3. Use Kubernetes cert-manager for automatic certificate management

---

## Summary

### Infrastructure Maturity Assessment

| Category | Current State | Maturity Level | Priority Actions |
|----------|---------------|----------------|------------------|
| **Containerization** | None | 0 - Not Started | Create Dockerfile, .dockerignore |
| **CI/CD** | None | 0 - Not Started | Implement GitHub Actions workflows |
| **Testing Automation** | Tests exist, not automated | 1 - Basic | Add CI test matrix |
| **Release Automation** | Manual | 0 - Not Started | Add release workflow |
| **Package Distribution** | Local only | 1 - Basic | Configure PyPI publishing |
| **Documentation** | README exists | 2 - Adequate | Add deployment docs |
| **Security Scanning** | None | 0 - Not Started | Add Trivy, dependency scanning |

### Overall Maturity Score: 1/5 (Initial)

The project has a solid Python package structure with good code quality tooling configured (ruff, mypy, pytest), but lacks all infrastructure components for production deployment and automated development workflows.

### Recommended Implementation Order

1. **Week 1 - Critical Infrastructure**
   - [ ] Create Dockerfile (multi-stage, security-hardened)
   - [ ] Create .dockerignore
   - [ ] Create root .gitignore
   - [ ] Add GitHub Actions CI workflow (lint, test, build)

2. **Week 2 - Development Experience**
   - [ ] Create docker-compose.yml for local development
   - [ ] Add Makefile with common commands
   - [ ] Test Docker builds locally

3. **Week 3 - Release Pipeline**
   - [ ] Configure PyPI trusted publishing
   - [ ] Add GitHub Actions release workflow
   - [ ] Create first tagged release

4. **Week 4 - Production Readiness**
   - [ ] Add security scanning (Trivy)
   - [ ] Add Kubernetes manifests (if applicable)
   - [ ] Document deployment procedures

### Quick Start Commands

After implementing the recommendations:

```bash
# Build Docker image
docker build -t exphttp:local .

# Run locally
docker run -p 8080:8080 exphttp:local

# Run with TLS
docker run -p 8443:8443 exphttp:local --tls --host 0.0.0.0 --port 8443

# Development with docker-compose
docker compose up -d

# Run tests in container
docker compose --profile test run --rm test
```

---

*Review performed by Infrastructure & DevOps cluster agents*
*Date: 2026-01-23*
