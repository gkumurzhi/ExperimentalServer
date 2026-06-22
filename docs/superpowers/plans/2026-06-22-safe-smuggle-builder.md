# Safe Lab-Only SMUGGLE Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing `SMUGGLE` flow with a safe `lab`-only builder for neutral internal test artifacts, including allowlisted output extensions, safe presets, bounded text overrides, and backward-compatible one-shot artifact generation.

**Architecture:** Keep the current `SMUGGLE /uploads/<file>` contract and add a bounded builder layer on top of it. The server remains authoritative: it validates query parameters, maps them into a closed builder config, renders one of a few fixed safe templates, and returns the same one-shot `smuggle_*.html` URL. The SPA replaces the narrow XOR-only modal with a richer builder modal that previews the safe artifact and sends only structured query params.

**Tech Stack:** Python server handlers, static SPA JavaScript/CSS, Playwright browser smoke, pytest

---

## File Map

- `src/utils/smuggling.py`
  Safe builder models, extension/preset allowlists, resolved download filename logic, and closed HTML renderer variants.
- `src/handlers/smuggle.py`
  Request-level parsing/validation for builder query params and handoff into the renderer.
- `src/data/static/ui/files.js`
  Expanded SMUGGLE builder modal, preview state, query-string construction, and result-dialog integration.
- `src/data/static/ui/core.js`
  RU/EN copy for builder labels, presets, validation hints, and visible test-artifact wording.
- `src/data/static/ui/components.css`
  Builder modal layout, preview card styles, and responsive behavior.
- `tests/test_smuggling_utils.py`
  Pure renderer/validation tests for safe builder config and generated HTML contracts.
- `tests/test_server_methods.py`
  Request/handler-level tests for accepted and rejected builder params, legacy compatibility, and encrypted compatibility.
- `tools/browser_smoke.playwright.js`
  End-to-end builder modal regression and download-filename verification in the real browser flow.
- `docs/api.md`
  Public API contract for safe builder query params.
- `docs/security.md`
  Lab-only scope and safe test-artifact boundary wording.

### Task 1: Add Safe Builder Render Models

**Files:**
- Modify: `src/utils/smuggling.py`
- Create: `tests/test_smuggling_utils.py`
- Test: `tests/test_smuggling_utils.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_smuggling_utils.py` with focused renderer coverage:

```python
from src.utils.smuggling import (
    SafeSmuggleBuilderConfig,
    generate_smuggling_html,
    resolve_safe_smuggle_download_filename,
)


def test_resolve_safe_smuggle_download_filename_uses_allowlisted_extension():
    filename = resolve_safe_smuggle_download_filename(
        source_filename="report.bin",
        download_name="Quarterly-Report",
        download_ext="pdf",
    )
    assert filename == "Quarterly-Report.pdf"


def test_generate_smuggling_html_card_auto_includes_notice_and_countdown():
    html = generate_smuggling_html(
        b"payload",
        "report.bin",
        builder=SafeSmuggleBuilderConfig(
            download_name="Quarterly-Report",
            download_ext="pdf",
            preset="card_auto",
            title="Quarterly Report",
            message="Internal lab test artifact",
            cta_label="Download test artifact",
            delay_ms=1200,
            show_notice=True,
        ),
    )
    assert "Quarterly-Report.pdf" in html
    assert "Internal lab test artifact" in html
    assert "Test artifact" in html
    assert "setTimeout(startDownload, 1200)" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_smuggling_utils.py -v`
Expected: FAIL because `SafeSmuggleBuilderConfig` and `resolve_safe_smuggle_download_filename()` do not exist yet and `generate_smuggling_html()` does not accept a `builder` keyword argument.

- [ ] **Step 3: Write minimal implementation**

Extend `src/utils/smuggling.py` with closed builder models and a safe renderer branch:

```python
SAFE_SMUGGLE_EXTENSIONS: tuple[str, ...] = ("txt", "bin", "dat", "zip", "pdf")
SAFE_SMUGGLE_PRESETS: tuple[str, ...] = ("direct", "card_manual", "card_auto")


@dataclass(frozen=True)
class SafeSmuggleBuilderConfig:
    download_name: str | None = None
    download_ext: str | None = None
    preset: str = "direct"
    title: str | None = None
    message: str | None = None
    cta_label: str | None = None
    delay_ms: int = 0
    show_notice: bool = True


def resolve_safe_smuggle_download_filename(
    source_filename: str,
    download_name: str | None,
    download_ext: str | None,
) -> str:
    stem = (download_name or source_filename.rsplit(".", 1)[0]).strip() or "download"
    ext = (download_ext or source_filename.rsplit(".", 1)[-1]).strip(".").lower()
    return f"{stem}.{ext}" if ext else stem


def generate_smuggling_html(
    file_data: bytes,
    filename: str,
    password: str | None = None,
    password_captcha: str | None = None,
    crypto_js_src: str = "/static/crypto-js.min.js",
    builder: SafeSmuggleBuilderConfig | None = None,
) -> str:
    resolved_filename = resolve_safe_smuggle_download_filename(
        filename,
        builder.download_name if builder else None,
        builder.download_ext if builder else None,
    )
    if password:
        encrypted = xor_encrypt(file_data, password)
        context = SmugglingRenderContext(
            filename=resolved_filename,
            base64_data=base64.b64encode(encrypted).decode("utf-8"),
            encrypted=True,
            password_captcha=password_captcha,
            options=SmugglingRenderOptions(crypto_js_src=crypto_js_src),
        )
    else:
        context = SmugglingRenderContext(
            filename=resolved_filename,
            base64_data=base64.b64encode(file_data).decode("utf-8"),
            encrypted=False,
        )
    return _render_safe_smuggling_html(context, builder) if builder else _render_smuggling_html(context)
```

Add one renderer branch per safe preset. Keep the existing legacy branches intact when `builder is None`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_smuggling_utils.py -v`
Expected: PASS with the resolved filename helper and safe-card renderer branch covered.

- [ ] **Step 5: Commit**

```bash
git add src/utils/smuggling.py tests/test_smuggling_utils.py
git commit -m "Add safe SMUGGLE builder render models"
```

### Task 2: Validate Builder Params in the SMUGGLE Handler

**Files:**
- Modify: `src/handlers/smuggle.py`
- Modify: `tests/test_server_methods.py`
- Test: `tests/test_server_methods.py`

- [ ] **Step 1: Write the failing tests**

Add targeted handler tests near the existing SMUGGLE coverage in `tests/test_server_methods.py`:

```python
def test_smuggle_builder_rejects_non_allowlisted_extension(self, server, upload_dir):
    (upload_dir / "small.txt").write_bytes(b"small payload")

    response = server.handle_smuggle(
        make_request(
            "SMUGGLE",
            "/uploads/small.txt?download_name=Quarterly-Report&download_ext=exe&preset=card_manual",
        )
    )

    assert response.status_code == 400
    body = json.loads(response.body)
    assert body["error"] == "Invalid SMUGGLE builder extension"


def test_smuggle_builder_card_auto_renders_selected_download_name(self, server, upload_dir):
    (upload_dir / "small.txt").write_bytes(b"small payload")

    response = server.handle_smuggle(
        make_request(
            "SMUGGLE",
            "/uploads/small.txt?download_name=Quarterly-Report&download_ext=pdf"
            "&preset=card_auto&title=Quarterly%20Report"
            "&message=Internal%20lab%20test%20artifact"
            "&cta_label=Download%20test%20artifact&delay_ms=1200&show_notice=1",
        )
    )

    assert response.status_code == 200
    body = json.loads(response.body)
    temp_path = upload_dir / body["url"].removeprefix("/uploads/")
    html = temp_path.read_text(encoding="utf-8")
    assert "Quarterly-Report.pdf" in html
    assert "Internal lab test artifact" in html
    assert "Test artifact" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_server_methods.py -k "smuggle_builder" -v`
Expected: FAIL because the current handler ignores builder query params and never rejects `download_ext=exe`.

- [ ] **Step 3: Write minimal implementation**

Parse builder query params in `src/handlers/smuggle.py`, validate them, and pass a resolved config into `generate_smuggling_html()`:

```python
from ..utils.smuggling import (
    SAFE_SMUGGLE_EXTENSIONS,
    SAFE_SMUGGLE_PRESETS,
    SafeSmuggleBuilderConfig,
    generate_smuggling_html,
)


def _parse_safe_smuggle_builder(self, request: HTTPRequest) -> SafeSmuggleBuilderConfig | None:
    query = request.query_params
    if not any(
        key in query
        for key in ("download_name", "download_ext", "preset", "title", "message", "cta_label", "delay_ms", "show_notice")
    ):
        return None

    download_ext = (query.get("download_ext") or "").strip().lower()
    if download_ext and download_ext not in SAFE_SMUGGLE_EXTENSIONS:
        raise ValueError("Invalid SMUGGLE builder extension")

    preset = (query.get("preset") or "direct").strip().lower()
    if preset not in SAFE_SMUGGLE_PRESETS:
        raise ValueError("Invalid SMUGGLE builder preset")

    delay_ms = int(query.get("delay_ms") or "0")
    if delay_ms < 0 or delay_ms > 10000:
        raise ValueError("Invalid SMUGGLE builder delay")

    return SafeSmuggleBuilderConfig(
        download_name=(query.get("download_name") or "").strip() or None,
        download_ext=download_ext or None,
        preset=preset,
        title=(query.get("title") or "").strip() or None,
        message=(query.get("message") or "").strip() or None,
        cta_label=(query.get("cta_label") or "").strip() or None,
        delay_ms=delay_ms,
        show_notice=query.get("show_notice", "1") != "0",
    )
```

Wrap `ValueError` in a stable `400` JSON response and preserve the legacy branch when no builder params are present.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_server_methods.py -k "smuggle_builder or smuggle_small_file_generates_registered_temp_html or smuggle_encrypted_response_exposes_verification_password" -v`
Expected: PASS for both the new builder-path tests and the legacy/encrypted compatibility checks.

- [ ] **Step 5: Commit**

```bash
git add src/handlers/smuggle.py tests/test_server_methods.py
git commit -m "Validate safe SMUGGLE builder query params"
```

### Task 3: Replace the Narrow Modal with the Safe Builder UI

**Files:**
- Modify: `src/data/static/ui/files.js`
- Modify: `src/data/static/ui/core.js`
- Modify: `src/data/static/ui/components.css`
- Modify: `tools/browser_smoke.playwright.js`
- Test: `tools/browser_smoke.playwright.js`

- [ ] **Step 1: Write the failing browser smoke regression**

Extend `tools/browser_smoke.playwright.js` so the SMUGGLE happy path expects builder fields and verifies the chosen download-facing filename:

```javascript
async function smuggleViaServerFilesAndAssert(name) {
  const actionButton = getServerFileAction(name, "smuggle");
  await actionButton.click();

  await page.locator("#smuggleDownloadName").waitFor({ state: "visible", timeout: 10000 });
  await page.locator("#smuggleDownloadExt").waitFor({ state: "visible", timeout: 10000 });
  await page.locator("#smugglePreset").waitFor({ state: "visible", timeout: 10000 });
  await page.locator("#smugglePreview").waitFor({ state: "visible", timeout: 10000 });

  await page.locator("#smuggleDownloadName").fill("Quarterly-Report");
  await page.locator("#smuggleDownloadExt").selectOption("pdf");
  await page.locator("#smugglePreset").selectOption("card_auto");
  await page.locator("#smuggleTitleInput").fill("Quarterly Report");
  await page.locator("#smuggleMessageInput").fill("Internal lab test artifact");
  await page.locator("#smuggleDelayMs").fill("1200");
  await page.locator("#smuggleSubmitBtn").click();

  const popupPromise = page.waitForEvent("popup", { timeout: 5000 });
  await page.locator("#smuggleOpenBtn").click();
  const popup = await popupPromise;
  await assertSmuggleArtifactPopupCompletes(popup, "Quarterly-Report.pdf");
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tools/browser_smoke.py --profile lab --mode full`
Expected: FAIL because the current SMUGGLE modal has only `#smuggleEncrypt`, `#smuggleSubmitBtn`, and `#smuggleCancelBtn`.

- [ ] **Step 3: Write minimal implementation**

Expand the modal in `src/data/static/ui/files.js`, add RU/EN copy in `src/data/static/ui/core.js`, and add layout styles in `src/data/static/ui/components.css`.

Use a bounded local state model and query construction:

```javascript
const SAFE_SMUGGLE_EXTENSIONS = ["txt", "bin", "dat", "zip", "pdf"];
const SAFE_SMUGGLE_PRESETS = {
  direct: { supportsDelay: false, supportsButton: false },
  card_manual: { supportsDelay: false, supportsButton: true },
  card_auto: { supportsDelay: true, supportsButton: true },
};

function getDefaultSmuggleBuilderState(filePath) {
  const sourceName = filePath.split("/").pop() || "artifact.bin";
  const dotIndex = sourceName.lastIndexOf(".");
  return {
    downloadName: dotIndex > 0 ? sourceName.slice(0, dotIndex) : sourceName,
    downloadExt: dotIndex > 0 ? sourceName.slice(dotIndex + 1).toLowerCase() : "bin",
    preset: "direct",
    title: t("smuggleBuilderDefaultTitle"),
    message: t("smuggleBuilderDefaultMessage"),
    ctaLabel: t("smuggleBuilderDefaultCta"),
    delayMs: 1200,
    showNotice: true,
    encrypt: false,
  };
}

function buildSmuggleRequestPath(filePath, state) {
  const params = new URLSearchParams();
  params.set("download_name", state.downloadName);
  params.set("download_ext", state.downloadExt);
  params.set("preset", state.preset);
  params.set("title", state.title);
  params.set("message", state.message);
  params.set("cta_label", state.ctaLabel);
  params.set("delay_ms", String(state.delayMs));
  params.set("show_notice", state.showNotice ? "1" : "0");
  if (state.encrypt) {
    params.set("encrypt", "1");
  }
  return `${filePath}?${params.toString()}`;
}
```

Wire the result dialog and popup verification to the selected download-facing filename rather than the original source filename.

- [ ] **Step 4: Run test to verify it passes**

Run: `python tools/browser_smoke.py --profile lab --mode full`
Expected: PASS with the expanded builder modal, preview, result dialog, and popup download filename all working.

- [ ] **Step 5: Commit**

```bash
git add src/data/static/ui/files.js \
  src/data/static/ui/core.js \
  src/data/static/ui/components.css \
  tools/browser_smoke.playwright.js
git commit -m "Add safe SMUGGLE builder modal"
```

### Task 4: Update Docs and Run Final Verification

**Files:**
- Modify: `docs/api.md`
- Modify: `docs/security.md`
- Test: `tests/test_smuggling_utils.py`
- Test: `tests/test_server_methods.py`
- Test: `tools/browser_smoke.playwright.js`

- [ ] **Step 1: Write the failing documentation expectation**

Update the docs sections that currently describe only legacy `SMUGGLE` so they now must mention safe builder params and the lab-only test-artifact boundary:

```markdown
## SMUGGLE

SMUGGLE may also receive safe lab-only builder params such as:

- `download_name`
- `download_ext`
- `preset`
- `title`
- `message`
- `cta_label`
- `delay_ms`
- `show_notice`
```

```markdown
- Safe SMUGGLE builder output is a neutral internal test artifact only.
- It does not support arbitrary HTML, external redirects, or deceptive prompts.
```

- [ ] **Step 2: Run verification to confirm docs are still incomplete**

Run: `python tools/check_stale_docs.py`
Expected: PASS or FAIL depending on current wording, but do not skip this step; read the output and use it to catch any stale references before editing.

- [ ] **Step 3: Write the minimal documentation updates**

Update `docs/api.md` and `docs/security.md` with the finalized contract and boundary wording. Keep the legacy request examples, then add one safe builder example:

```http
SMUGGLE /uploads/report.bin?download_name=Quarterly-Report&download_ext=pdf&preset=card_auto&title=Quarterly%20Report&message=Internal%20lab%20test%20artifact&cta_label=Download&delay_ms=1200&show_notice=1 HTTP/1.1
```

Document:

- the fixed extension allowlist
- the three safe presets
- the visible test-artifact marker requirement
- backward compatibility for legacy `SMUGGLE`

- [ ] **Step 4: Run final verification**

Run:

```bash
pytest tests/test_smuggling_utils.py tests/test_server_methods.py -v
python tools/browser_smoke.py --profile lab --mode full
python tools/check_stale_docs.py
```

Expected:

- pytest: PASS
- browser smoke: PASS
- stale docs checker: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/api.md docs/security.md
git commit -m "Document safe SMUGGLE builder"
```
