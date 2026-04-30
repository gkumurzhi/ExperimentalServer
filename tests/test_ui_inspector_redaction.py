"""Regression coverage for the browser inspector redaction policy."""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def inspector_probe() -> dict[str, str]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is required for inspector JavaScript regression coverage")

    script = textwrap.dedent(
        r"""
        const fs = require("fs");
        const vm = require("vm");

        const source = fs.readFileSync("src/data/static/ui/inspector.js", "utf8");
        const context = {
          console,
          localStorage: { getItem: () => "raw" },
          document: {
            addEventListener: () => {},
            getElementById: () => null,
            querySelector: () => null,
          },
          t: (key) => ({
            exchangeRedacted: "REDACTED",
            exchangeRequestEmpty: "request empty",
            exchangeResponseEmpty: "response empty",
            requestPreviewNoBody: "no body",
            headersNA: "n/a",
            exchangeBodyKind: "Body kind",
            responseSummaryFieldContentType: "Content-Type",
            requestPreviewFieldBodySize: "Body size",
          })[key] || key,
          formatSize: (value) => `${value} B`,
          parseJsonSafe: (text) => {
            try {
              return JSON.parse(text);
            } catch (_error) {
              return null;
            }
          },
          esc: (value) => String(value),
          formatHttpStatusLabel: (status, text) => `${status} ${text || ""}`.trim(),
        };

        vm.createContext(context);
        vm.runInContext(source, context);
        const result = vm.runInContext(`
          (() => {
            const advancedArea = {
              id: "opsecExchangeRequest",
              dataset: {},
              textContent: "",
              innerHTML: "",
            };
            const advancedMessage = {
              transport: "http",
              method: "XUPLOAD",
              path: "/upload?d=url-payload&k=test-password&n=visible.txt",
              headers: {
                "X-D": "header-payload",
                "X-D-0": "chunk-payload",
                "X-D-alpha": "named-chunk-payload",
                "X-K": "test-password",
                "X-N": "visible.txt",
              },
              body: createExchangeTextBody(
                JSON.stringify({
                  d: "body-payload",
                  k: "test-password",
                  n: "visible.txt",
                }),
                { contentType: "application/json" },
              ),
            };
            renderExchangePane(advancedArea, advancedMessage, "request");
            setExchangeInspector("opsec", {
              phase: "complete",
              request: advancedMessage,
              response: {
                transport: "http",
                method: "XUPLOAD",
                path: "/upload",
                body: createExchangeTextBody("ok"),
              },
            });

            const previewRaw = buildExchangeRawMessage({
              transport: "http",
              method: "XUPLOAD",
              path: "/headers",
              body: createExchangePreviewBody({
                label: "headers",
                text: "X-D-0: preview-payload\\nX-K: preview-password\\nX-N: preview.txt",
              }),
            }, "request");

            const transcriptRaw = buildExchangeRawMessage({
              rawText: [
                "XUPLOAD /raw?d=transcript-url-payload&k=transcript-password HTTP/1.1",
                "X-D-alpha: transcript-header-payload",
                "X-K: transcript-password",
                "",
                JSON.stringify({
                  d: "transcript-body-payload",
                  k: "transcript-password",
                  n: "transcript.txt",
                }),
              ].join("\\n"),
            }, "request");

            const notepadMessage = {
              transport: "ws",
              type: "save",
              path: "/notes/ws",
              body: createExchangeJsonBody(
                {
                  type: "save",
                  sessionId: "session-secret",
                  data: "ciphertext-secret",
                  clientPublicKey: "client-key-secret",
                  serverPublicKey: "server-key-secret",
                  title: "Visible title",
                },
                {
                  rawText: JSON.stringify({
                    type: "save",
                    sessionId: "session-secret",
                    data: "ciphertext-secret",
                    clientPublicKey: "client-key-secret",
                    serverPublicKey: "server-key-secret",
                    title: "Visible title",
                  }),
                },
              ),
            };
            const notepadRaw = buildExchangeRawMessage(notepadMessage, "request");
            setExchangeInspector("notepad", {
              phase: "complete",
              request: notepadMessage,
              response: {
                transport: "ws",
                type: "saved",
                path: "/notes/ws",
                body: createExchangeJsonBody({ success: true }),
              },
            });

            return {
              advancedRaw: advancedArea.textContent,
              advancedCopyText: getExchangeAreaRawText("opsecExchangeRequest"),
              advancedDatasetPath: advancedArea.dataset.exchangePath,
              advancedStoredState: JSON.stringify(exchangeInspectorStates.get("opsec")),
              previewRaw,
              transcriptRaw,
              notepadRaw,
              notepadStoredState: JSON.stringify(exchangeInspectorStates.get("notepad")),
            };
          })()
        `, context);

        console.log(JSON.stringify(result));
        """
    )
    result = subprocess.run(
        [node, "-e", script],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"inspector JS probe failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    return json.loads(result.stdout)


def test_inspector_redacts_advanced_upload_raw_and_copy_output(
    inspector_probe: dict[str, str],
) -> None:
    combined = "\n".join(
        [
            inspector_probe["advancedRaw"],
            inspector_probe["advancedCopyText"],
            inspector_probe["advancedDatasetPath"],
            inspector_probe["advancedStoredState"],
            inspector_probe["previewRaw"],
            inspector_probe["transcriptRaw"],
        ]
    )

    for secret in (
        "test-password",
        "url-payload",
        "header-payload",
        "chunk-payload",
        "named-chunk-payload",
        "body-payload",
        "preview-payload",
        "preview-password",
        "transcript-password",
        "transcript-url-payload",
        "transcript-header-payload",
        "transcript-body-payload",
    ):
        assert secret not in combined

    assert inspector_probe["advancedRaw"] == inspector_probe["advancedCopyText"]
    assert "[REDACTED]" in combined
    assert "visible.txt" in combined
    assert "preview.txt" in combined


def test_inspector_redacts_notepad_session_key_and_data_fields(
    inspector_probe: dict[str, str],
) -> None:
    notepad_raw = inspector_probe["notepadRaw"]
    notepad_state = inspector_probe["notepadStoredState"]

    for secret in (
        "session-secret",
        "ciphertext-secret",
        "client-key-secret",
        "server-key-secret",
    ):
        assert secret not in notepad_raw
        assert secret not in notepad_state

    assert "[REDACTED]" in notepad_raw
    assert "[REDACTED]" in notepad_state
    assert "Visible title" in notepad_raw
    assert "Visible title" in notepad_state
