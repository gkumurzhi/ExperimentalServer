async (page) => {
  const unavailableUrl = __EXPHTTP_UNAVAILABLE_URL__;
  const uploadFilePath = __EXPHTTP_UPLOAD_FILE__;
  const opsecUploadUrlBoundaryFilePath = __EXPHTTP_OPSEC_UPLOAD_URL_BOUNDARY_FILE__;
  const opsecUploadFilePath = __EXPHTTP_OPSEC_UPLOAD_FILE__;
  const opsecUploadBoundaryFilePath = __EXPHTTP_OPSEC_UPLOAD_BOUNDARY_FILE__;
  const opsecUploadLargeFilePath = __EXPHTTP_OPSEC_UPLOAD_LARGE_FILE__;

  async function waitForSpaReady() {
    await page.waitForLoadState("domcontentloaded");
    await page.locator("#pathInput").waitFor({ state: "visible" });
    await page.locator("#uploadBtn").waitFor({ state: "attached" });
  }

  async function installClipboardMock() {
    const installMock = () => {
      window.__exphttpBrowserClipboardText = String(window.__exphttpBrowserClipboardText || "");
      if (window.__exphttpClipboardMockInstalled) {
        return;
      }

      const clipboard = {
        writeText: async (text) => {
          window.__exphttpBrowserClipboardText = String(text ?? "");
        },
        readText: async () => String(window.__exphttpBrowserClipboardText || ""),
      };

      Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        get: () => clipboard,
      });

      window.__exphttpClipboardMockInstalled = true;
    };

    await page.addInitScript(installMock);
    await page.evaluate(installMock);
  }

  async function waitForPageCondition(label, pageFunction, arg = null, timeout = 10000) {
    try {
      await page.waitForFunction(pageFunction, arg, { timeout });
    } catch (error) {
      throw new Error(`${label}: ${error.message}`);
    }
  }

  async function waitForText(locator, textOrPattern, timeout = 10000) {
    await locator.waitFor({ state: "attached", timeout });
    const selector = await locator.evaluate((node) => {
      if (!node.id) {
        throw new Error("waitForText requires a locator with an id-backed element");
      }
      return `#${node.id}`;
    });
    const isRegex = textOrPattern instanceof RegExp;
    const expected = isRegex ? textOrPattern.source : textOrPattern;
    const flags = isRegex ? textOrPattern.flags : "";
    await waitForPageCondition(
      `waitForText(${selector})`,
      ([targetSelector, targetText, targetFlags, targetIsRegex]) => {
        const matcher = targetIsRegex ? new RegExp(targetText, targetFlags) : null;
        const element = document.querySelector(targetSelector);
        if (!element) {
          return false;
        }
        const content = element.innerText;
        return matcher ? matcher.test(content) : content.includes(targetText);
      },
      [selector, expected, flags, isRegex],
      timeout
    );
  }

  async function waitForLiveRegionText(regionId, textOrPattern, timeout = 10000) {
    const isRegex = textOrPattern instanceof RegExp;
    const expected = isRegex ? textOrPattern.source : textOrPattern;
    const flags = isRegex ? textOrPattern.flags : "";
    await waitForPageCondition(
      `waitForLiveRegionText(${regionId})`,
      ([targetRegionId, targetText, targetFlags, targetIsRegex]) => {
        const region = document.getElementById(targetRegionId);
        if (!region) {
          return false;
        }
        const content = region.innerText || region.textContent || "";
        if (targetIsRegex) {
          return new RegExp(targetText, targetFlags).test(content);
        }
        return content.includes(targetText);
      },
      [regionId, expected, flags, isRegex],
      timeout
    );
  }

  async function waitForValue(selector, expected, timeout = 10000) {
    await waitForPageCondition(
      `waitForValue(${selector})`,
      ([targetSelector, targetValue]) => {
        const element = document.querySelector(targetSelector);
        return Boolean(element && "value" in element && element.value === targetValue);
      },
      [selector, expected],
      timeout
    );
  }

  async function confirmAppDialog(expectedTextOrPattern, timeout = 10000) {
    const dialog = page.locator('#appDialog [role="alertdialog"]');
    await dialog.waitFor({ state: "visible", timeout });
    if (expectedTextOrPattern) {
      const isRegex = expectedTextOrPattern instanceof RegExp;
      const expected = isRegex ? expectedTextOrPattern.source : expectedTextOrPattern;
      const flags = isRegex ? expectedTextOrPattern.flags : "";
      await waitForPageCondition(
        "confirmAppDialog text",
        ([targetText, targetFlags, targetIsRegex]) => {
          const root = document.getElementById("appDialog");
          if (!root) {
            return false;
          }
          const content = root.innerText;
          if (targetIsRegex) {
            return new RegExp(targetText, targetFlags).test(content);
          }
          return content.includes(targetText);
        },
        [expected, flags, isRegex],
        timeout
      );
    }
    await page.locator('#appDialog [data-dialog-action="confirm"]').click();
    await page.locator("#appDialog").waitFor({ state: "detached", timeout });
  }

  async function waitForConnectionStatus(expectedState, expectedTransport, timeout = 10000) {
    await waitForPageCondition(
      `waitForConnectionStatus(${expectedState},${expectedTransport})`,
      ([state, transport]) => {
        const element = document.getElementById("notepadConnStatus");
        return Boolean(
          element &&
          element.dataset &&
          element.dataset.state === state &&
          element.dataset.transport === transport
        );
      },
      [expectedState, expectedTransport],
      timeout
    );
  }

  async function switchLanguage(lang, timeout = 10000) {
    const selector = lang === "en" ? "#langEn" : "#langRu";
    await page.locator(selector).click();
    await waitForPageCondition(
      `switchLanguage(${lang})`,
      ([targetLang, targetSelector]) => {
        const button = document.querySelector(targetSelector);
        return Boolean(
          document.documentElement.lang === targetLang &&
          button &&
          button.classList.contains("active")
        );
      },
      [lang, selector],
      timeout
    );
  }

  async function assertOutputLiveRegionContracts(timeout = 10000) {
    await waitForPageCondition(
      "assertOutputLiveRegionContracts",
      () => {
        const panelIds = ["responseArea", "uploadResponseArea", "filesResponseArea", "opsecResponseArea"];
        const liveIds = ["responseAreaLive", "uploadResponseAreaLive", "filesResponseAreaLive", "opsecResponseAreaLive"];

        const panelsOk = panelIds.every((id) => {
          const panel = document.getElementById(id);
          return Boolean(panel && !panel.hasAttribute("aria-live"));
        });

        const liveOk = liveIds.every((id) => {
          const region = document.getElementById(id);
          return Boolean(
            region &&
            region.getAttribute("role") === "status" &&
            region.getAttribute("aria-live") === "polite" &&
            region.getAttribute("aria-atomic") === "true"
          );
        });

        const opsecWarning = document.getElementById("opsecTransportWarning");
        const opsecWarningOk = Boolean(
          opsecWarning &&
          opsecWarning.getAttribute("role") === "status" &&
          opsecWarning.getAttribute("aria-live") === "polite" &&
          opsecWarning.getAttribute("aria-atomic") === "true"
        );

        return panelsOk && liveOk && opsecWarningOk;
      },
      null,
      timeout
    );
  }

  async function waitForTabState(tabName, options = {}, timeout = 10000) {
    const { focused = false } = options;
    await waitForPageCondition(
      `waitForTabState(${tabName})`,
      ([targetTabName, targetFocused]) => {
        const tabs = Array.from(document.querySelectorAll('.tab[role="tab"][data-tab-target]'));
        const panels = Array.from(document.querySelectorAll('.tab-content[role="tabpanel"]'));
        const activeTab = document.getElementById(`tab-${targetTabName}`);
        const activePanel = document.getElementById(`${targetTabName}-tab`);

        if (!activeTab || !activePanel) {
          return false;
        }

        const activeTabOk =
          activeTab.classList.contains("active") &&
          activeTab.getAttribute("aria-selected") === "true" &&
          activeTab.getAttribute("tabindex") === "0";
        const activePanelOk = activePanel.classList.contains("active") && activePanel.hidden === false;
        const inactiveTabsOk = tabs.every((tab) =>
          tab === activeTab ||
          (!tab.classList.contains("active") &&
            tab.getAttribute("aria-selected") === "false" &&
            tab.getAttribute("tabindex") === "-1")
        );
        const inactivePanelsOk = panels.every((panel) =>
          panel === activePanel || (panel.classList.contains("active") === false && panel.hidden === true)
        );
        const focusOk = !targetFocused || document.activeElement === activeTab;

        return activeTabOk && activePanelOk && inactiveTabsOk && inactivePanelsOk && focusOk;
      },
      [tabName, focused],
      timeout
    );
  }

  async function waitForUploadMethodState(method, options = {}, timeout = 10000) {
    const { focused = false } = options;
    await waitForPageCondition(
      `waitForUploadMethodState(${method})`,
      ([targetMethod, targetFocused]) => {
        const buttons = Array.from(document.querySelectorAll('.upload-method-btn[data-upload-method]'));
        const activeButton = buttons.find((button) => button.dataset.uploadMethod === targetMethod);
        if (!activeButton) {
          return false;
        }

        const activeOk =
          activeButton.classList.contains("active") &&
          activeButton.getAttribute("aria-checked") === "true" &&
          activeButton.getAttribute("tabindex") === "0";
        const inactiveOk = buttons.every((button) =>
          button === activeButton ||
          (!button.classList.contains("active") &&
            button.getAttribute("aria-checked") === "false" &&
            button.getAttribute("tabindex") === "-1")
        );
        const hint = document.getElementById("uploadMethodHint");
        const hintOk = Boolean(hint && hint.innerText.includes(targetMethod));
        const focusOk = !targetFocused || document.activeElement === activeButton;

        return activeOk && inactiveOk && hintOk && focusOk;
      },
      [method, focused],
      timeout
    );
  }

  async function assertLocaleSnapshot({
    uploadTabText,
    filesTabText,
    opsecTabText,
    noteListText,
    charCountText,
    themeLabel,
  }) {
    await waitForText(page.locator("#tab-upload"), uploadTabText);
    await waitForText(page.locator("#tab-files"), filesTabText);
    await waitForText(page.locator("#tab-opsec"), opsecTabText);
    await waitForPageCondition("upload tabs are adjacent", () => {
      const ids = Array.from(document.querySelectorAll(".tool-tabs .tab")).map((tab) => tab.id);
      return ids.join(",") === "tab-upload,tab-opsec,tab-files,tab-notepad";
    });
    await waitForText(page.locator("#notepadNoteList"), noteListText);
    await waitForText(page.locator("#notepadCharCount"), charCountText);
    await waitForPageCondition(
      `theme button translated (${themeLabel})`,
      ([expectedLabel]) => {
        const button = document.getElementById("themeBtn");
        return Boolean(
          button &&
          button.title === expectedLabel &&
          button.getAttribute("aria-label") === expectedLabel
        );
      },
      [themeLabel],
      10000
    );
  }

  async function uploadViaDom(name) {
    await page.locator("#tab-upload").click();
    await page.locator("#fileInput").setInputFiles(uploadFilePath);

    await waitForPageCondition("upload button enabled", () => {
      const uploadBtn = document.getElementById("uploadBtn");
      return Boolean(uploadBtn && !uploadBtn.disabled);
    }, null, 10000);

    await page.locator("#uploadBtn").click();
    await waitForText(page.locator("#uploadResponseArea"), name);
  }

  async function browseUploadsAndAssert(name) {
    await page.locator("#tab-files").click();
    await waitForTabState("files", { focused: true });
    await page.locator("#browsePathInput").fill("/uploads");
    await page.getByRole("button", { name: /^(Обзор(?: \(INFO\))?|Browse(?: \(INFO\))?)$/ }).click();
    await waitForText(page.locator("#serverFiles"), name);
  }

  async function waitForRequestPanelResponse(method, status, path, timeout = 15000) {
    await waitForPageCondition(
      `waitForRequestPanelResponse(${method},${status},${path})`,
      ([targetMethod, targetStatus, targetPath]) => {
        const responseArea = document.getElementById("responseArea");
        return Boolean(
          responseArea &&
          responseArea.dataset.requestPhase === "complete" &&
          responseArea.dataset.requestMethod === targetMethod &&
          responseArea.dataset.requestStatus === String(targetStatus) &&
          responseArea.dataset.requestPath === targetPath
        );
      },
      [method, status, path],
      timeout
    );
  }

  async function waitForRequestPreview(method, path, timeout = 15000) {
    await waitForPageCondition(
      `waitForRequestPreview(${method},${path})`,
      ([targetMethod, targetPath]) => {
        const section = document.getElementById("requestPreviewSection");
        const previewArea = document.getElementById("requestPreviewArea");
        return Boolean(
          section &&
          previewArea &&
          section.hidden === false &&
          previewArea.dataset.requestPhase === "ready" &&
          previewArea.dataset.requestMethod === targetMethod &&
          previewArea.dataset.requestPath === targetPath
        );
      },
      [method, path],
      timeout
    );
  }

  async function assertRequestPreviewToggleState(expectedChecked, expectedVisible, timeout = 10000) {
    await waitForPageCondition(
      `assertRequestPreviewToggleState(${expectedChecked},${expectedVisible})`,
      ([targetChecked, targetVisible]) => {
        const toggle = document.getElementById("requestPreviewToggle");
        const section = document.getElementById("requestPreviewSection");
        return Boolean(
          toggle &&
          section &&
          toggle.checked === targetChecked &&
          (section.hidden === !targetVisible)
        );
      },
      [expectedChecked, expectedVisible],
      timeout
    );
  }

  async function assertRequestPreviewModeState(expectedMode, timeout = 10000) {
    await waitForPageCondition(
      `assertRequestPreviewModeState(${expectedMode})`,
      ([targetMode]) => {
        const buttons = Array.from(document.querySelectorAll("[data-request-preview-mode]"));
        const previewArea = document.getElementById("requestPreviewArea");
        return Boolean(
          previewArea &&
          previewArea.dataset.requestView === targetMode &&
          buttons.length === 2 &&
          buttons.every((button) => {
            const isActive = button.dataset.requestPreviewMode === targetMode;
            return (
              button.classList.contains("active") === isActive &&
              button.getAttribute("aria-checked") === String(isActive) &&
              button.getAttribute("tabindex") === (isActive ? "0" : "-1")
            );
          })
        );
      },
      [expectedMode],
      timeout
    );
  }

  async function assertResponseViewState(expectedMode, timeout = 10000) {
    await waitForPageCondition(
      `assertResponseViewState(${expectedMode})`,
      ([targetMode]) => {
        const responseArea = document.getElementById("responseArea");
        return Boolean(responseArea && responseArea.dataset.requestView === targetMode);
      },
      [expectedMode],
      timeout
    );
  }

  async function assertClipboardSnapshot(kind, expectedText = [], timeout = 10000) {
    await waitForPageCondition(
      `assertClipboardSnapshot(${kind})`,
      ([targetKind]) => {
        const state = window.__exphttpClipboardState;
        return Boolean(
          state &&
          state.lastKind === targetKind &&
          typeof state.lastText === "string" &&
          state.lastText.length > 0
        );
      },
      [kind],
      timeout
    );

    const snapshot = await page.evaluate(() => ({
      clipboardText: String(window.__exphttpBrowserClipboardText || ""),
      lastText: String(window.__exphttpClipboardState?.lastText || ""),
      lastKind: String(window.__exphttpClipboardState?.lastKind || ""),
    }));

    if (snapshot.lastKind !== kind) {
      throw new Error(`Clipboard kind mismatch for ${kind}: ${snapshot.lastKind}`);
    }
    if (snapshot.lastText !== snapshot.clipboardText) {
      throw new Error(`Clipboard text mismatch for ${kind}`);
    }

    for (const item of expectedText) {
      if (!snapshot.lastText.includes(item)) {
        throw new Error(`Clipboard text for ${kind} missing "${item}": ${snapshot.lastText}`);
      }
    }
  }

  async function assertRequestBatchExport({
    phase,
    total,
    completed,
    matchCount,
    mismatchCount,
    failedCount,
    expectedMethods = [],
    expectedAttemptCounts = {},
    timeout = 10000,
  }) {
    await waitForPageCondition(
      "request batch export enabled",
      () => {
        const button = document.getElementById("requestBatchExportBtn");
        return Boolean(button && !button.disabled);
      },
      null,
      timeout
    );

    const downloadPromise = page.waitForEvent("download");
    await page.locator("#requestBatchExportBtn").click();
    const download = await downloadPromise;
    const suggestedFilename = download.suggestedFilename();

    await waitForPageCondition(
      "request batch export state",
      () => {
        const state = window.__exphttpBatchExportState;
        return Boolean(state && state.filename && state.content);
      },
      null,
      timeout
    );

    const snapshot = await page.evaluate(() => ({
      filename: String(window.__exphttpBatchExportState?.filename || ""),
      content: String(window.__exphttpBatchExportState?.content || ""),
    }));

    if (snapshot.filename !== suggestedFilename) {
      throw new Error(`Batch export filename mismatch: ${snapshot.filename} !== ${suggestedFilename}`);
    }
    if (!/^request-run-summary-.*\.json$/.test(snapshot.filename)) {
      throw new Error(`Unexpected batch export filename: ${snapshot.filename}`);
    }

    let report;
    try {
      report = JSON.parse(snapshot.content);
    } catch (error) {
      throw new Error(`Batch export content is not valid JSON: ${error.message}`);
    }

    if (
      report.phase !== phase ||
      report.total !== total ||
      report.completed !== completed ||
      report.summary?.matchCount !== matchCount ||
      report.summary?.mismatchCount !== mismatchCount ||
      report.summary?.failedCount !== failedCount
    ) {
      throw new Error(`Unexpected batch export summary: ${snapshot.content}`);
    }

    if (!Array.isArray(report.results) || report.results.length !== total) {
      throw new Error(`Unexpected batch export result count: ${snapshot.content}`);
    }

    for (const method of expectedMethods) {
      if (!report.results.some((result) => result.method === method)) {
        throw new Error(`Batch export is missing method ${method}: ${snapshot.content}`);
      }
    }

    for (const [method, expectedAttemptCount] of Object.entries(expectedAttemptCounts)) {
      const result = report.results.find((item) => item.method === method);
      if (!result) {
        throw new Error(`Batch export is missing method ${method} for attempts check: ${snapshot.content}`);
      }
      if (!Array.isArray(result.attempts) || result.attempts.length !== expectedAttemptCount) {
        throw new Error(`Unexpected attempt count for ${method}: ${snapshot.content}`);
      }
      if (
        result.attempts.some((attempt) => (
          attempt.method !== method ||
          typeof attempt.path !== "string" ||
          typeof attempt.expectedStatus !== "string" ||
          typeof attempt.actualStatus !== "string" ||
          typeof attempt.checkState !== "string" ||
          typeof attempt.checkLabel !== "string" ||
          typeof attempt.timestamp !== "string"
        ))
      ) {
        throw new Error(`Invalid attempt payload for ${method}: ${snapshot.content}`);
      }
    }
  }

  async function assertRequestBatchIssuesFilter({
    checked,
    filter,
    visibleCount,
    emptyText = "",
    timeout = 10000,
  }) {
    await waitForPageCondition(
      `assertRequestBatchIssuesFilter(${filter},${visibleCount})`,
      ([targetChecked, targetFilter, targetVisibleCount, targetEmptyText]) => {
        const toggle = document.getElementById("requestBatchIssuesOnlyToggle");
        const summary = document.getElementById("requestBatchSummary");
        const rows = Array.from(document.querySelectorAll("#requestBatchSummary .request-batch-summary__row"));
        const empty = summary?.querySelector(".request-batch-summary__empty");

        return Boolean(
          toggle &&
          summary &&
          toggle.checked === targetChecked &&
          summary.dataset.batchFilter === targetFilter &&
          summary.dataset.batchVisibleCount === String(targetVisibleCount) &&
          rows.length === targetVisibleCount &&
          (
            targetEmptyText
              ? empty && (empty.textContent || "").includes(targetEmptyText)
              : !empty
          )
        );
      },
      [checked, filter, visibleCount, emptyText],
      timeout
    );
  }

  async function assertRequestMethodButtonBatchState({
    method,
    checkState,
    expectedStatus,
    actualStatus,
    timeout = 10000,
  }) {
    await waitForPageCondition(
      `assertRequestMethodButtonBatchState(${method},${checkState})`,
      ([targetMethod, targetCheckState, targetExpectedStatus, targetActualStatus]) => {
        const button = document.querySelector(`.request-method-switch [data-request-method="${targetMethod}"]`);
        const label = button?.getAttribute("aria-label") || "";
        const title = button?.getAttribute("title") || "";
        return Boolean(
          button &&
          button.dataset.batchCheck === targetCheckState &&
          button.dataset.batchExpectedStatus === targetExpectedStatus &&
          button.dataset.batchActualStatus === targetActualStatus &&
          label.includes(targetExpectedStatus) &&
          label.includes(targetActualStatus) &&
          title === label
        );
      },
      [method, checkState, expectedStatus, actualStatus],
      timeout
    );
  }

  async function assertRequestBatchCleared(timeout = 10000) {
    await waitForPageCondition(
      "request batch cleared",
      () => {
        const summary = document.getElementById("requestBatchSummary");
        const exportBtn = document.getElementById("requestBatchExportBtn");
        const rerunIssuesBtn = document.getElementById("requestBatchRerunIssuesBtn");
        const clearBtn = document.getElementById("requestBatchClearBtn");
        const issuesToggle = document.getElementById("requestBatchIssuesOnlyToggle");
        const batchStatus = document.getElementById("requestBatchStatus");
        const methodButtons = Array.from(document.querySelectorAll(".request-method-switch [data-request-method]"));

        return Boolean(
          summary &&
          summary.hidden === true &&
          summary.dataset.batchPhase === "idle" &&
          summary.dataset.batchTotal === "0" &&
          summary.dataset.batchCompleted === "0" &&
          summary.dataset.batchMatchCount === "0" &&
          summary.dataset.batchMismatchCount === "0" &&
          summary.dataset.batchFailedCount === "0" &&
          summary.dataset.batchVisibleCount === "0" &&
          exportBtn &&
          exportBtn.disabled &&
          rerunIssuesBtn &&
          rerunIssuesBtn.disabled &&
          rerunIssuesBtn.dataset.batchIssueCount === "0" &&
          clearBtn &&
          clearBtn.disabled &&
          issuesToggle &&
          !issuesToggle.checked &&
          batchStatus &&
          (batchStatus.textContent || "").trim() === "" &&
          typeof window.__exphttpBatchExportState === "undefined" &&
          methodButtons.length > 0 &&
          methodButtons.every((button) =>
            !button.dataset.batchCheck &&
            !button.dataset.batchExpectedStatus &&
            !button.dataset.batchActualStatus &&
            !button.hasAttribute("aria-label")
          )
        );
      },
      null,
      timeout
    );
  }

  async function assertRequestBatchRerunIssuesButtonState({
    disabled,
    issueCount,
    timeout = 10000,
  }) {
    await waitForPageCondition(
      `assertRequestBatchRerunIssuesButtonState(${disabled},${issueCount})`,
      ([targetDisabled, targetIssueCount]) => {
        const button = document.getElementById("requestBatchRerunIssuesBtn");
        const label = button?.getAttribute("aria-label") || "";
        const title = button?.getAttribute("title") || "";
        return Boolean(
          button &&
          button.disabled === targetDisabled &&
          button.dataset.batchIssueCount === String(targetIssueCount) &&
          title === label &&
          (
            targetIssueCount > 0
              ? label.includes(String(targetIssueCount))
              : label.length > 0
          )
        );
      },
      [disabled, issueCount],
      timeout
    );
  }

  async function assertRequestPreviewSummary(method, path, expectedText = [], timeout = 10000) {
    await waitForPageCondition(
      `assertRequestPreviewSummary(${method},${path})`,
      ([targetMethod, targetPath]) => {
        const previewArea = document.getElementById("requestPreviewArea");
        const summaryRoot = previewArea?.querySelector(".request-preview-summary");
        const content = previewArea?.innerText || "";
        return Boolean(
          previewArea &&
          summaryRoot &&
          previewArea.dataset.requestPhase === "ready" &&
          previewArea.dataset.requestMethod === targetMethod &&
          previewArea.dataset.requestPath === targetPath &&
          previewArea.dataset.requestView === "summary" &&
          !content.includes(`${targetMethod} ${targetPath} HTTP/1.1`)
        );
      },
      [method, path],
      timeout
    );

    const previewText = (await page.locator("#requestPreviewArea").innerText()).trim();
    for (const item of expectedText) {
      if (!previewText.includes(item)) {
        throw new Error(`Request preview summary missing "${item}": ${previewText}`);
      }
    }
  }

  async function assertResponseSummary(method, path, expectedText = [], timeout = 10000) {
    await waitForPageCondition(
      `assertResponseSummary(${method},${path})`,
      ([targetMethod, targetPath]) => {
        const responseArea = document.getElementById("responseArea");
        const summaryRoot = responseArea?.querySelector(".response-summary");
        return Boolean(
          responseArea &&
          summaryRoot &&
          responseArea.dataset.requestPhase === "complete" &&
          responseArea.dataset.requestMethod === targetMethod &&
          responseArea.dataset.requestPath === targetPath &&
          responseArea.dataset.requestView === "summary"
        );
      },
      [method, path],
      timeout
    );

    const responseText = (await page.locator("#responseArea").innerText()).trim();
    for (const item of expectedText) {
      if (!responseText.includes(item)) {
        throw new Error(`Response summary missing "${item}": ${responseText}`);
      }
    }
  }

  async function assertResponseRaw(method, path, expectedText = [], timeout = 10000) {
    await waitForPageCondition(
      `assertResponseRaw(${method},${path})`,
      ([targetMethod, targetPath]) => {
        const responseArea = document.getElementById("responseArea");
        const summaryRoot = responseArea?.querySelector(".response-summary");
        return Boolean(
          responseArea &&
          !summaryRoot &&
          responseArea.dataset.requestPhase === "complete" &&
          responseArea.dataset.requestMethod === targetMethod &&
          responseArea.dataset.requestPath === targetPath &&
          responseArea.dataset.requestView === "raw"
        );
      },
      [method, path],
      timeout
    );

    const responseText = (await page.locator("#responseArea").innerText()).trim();
    for (const item of expectedText) {
      if (!responseText.includes(item)) {
        throw new Error(`Raw response missing "${item}": ${responseText}`);
      }
    }
  }

  async function assertRequestPreviewComparison({
    method,
    path,
    expectedStatus,
    actualStatus,
    checkState,
    timeout = 10000,
  }) {
    await waitForPageCondition(
      `assertRequestPreviewComparison(${method},${path},${checkState})`,
      ([targetMethod, targetPath, targetExpectedStatus, targetActualStatus, targetCheckState]) => {
        const previewArea = document.getElementById("requestPreviewArea");
        return Boolean(
          previewArea &&
          previewArea.dataset.requestPhase === "ready" &&
          previewArea.dataset.requestMethod === targetMethod &&
          previewArea.dataset.requestPath === targetPath &&
          previewArea.dataset.requestView === "summary" &&
          previewArea.dataset.requestExpectedStatus === targetExpectedStatus &&
          previewArea.dataset.requestActualStatus === targetActualStatus &&
          previewArea.dataset.requestStatusCheck === targetCheckState
        );
      },
      [method, path, expectedStatus, actualStatus, checkState],
      timeout
    );
  }

  async function waitForRequestBatchSummary({
    phase,
    total,
    completed,
    matchCount,
    mismatchCount,
    failedCount,
    timeout = 60000,
  }) {
    await waitForPageCondition(
      `waitForRequestBatchSummary(${phase})`,
      ([targetPhase, targetTotal, targetCompleted, targetMatchCount, targetMismatchCount, targetFailedCount]) => {
        const summary = document.getElementById("requestBatchSummary");
        return Boolean(
          summary &&
          summary.hidden === false &&
          summary.dataset.batchPhase === targetPhase &&
          summary.dataset.batchTotal === String(targetTotal) &&
          summary.dataset.batchCompleted === String(targetCompleted) &&
          summary.dataset.batchMatchCount === String(targetMatchCount) &&
          summary.dataset.batchMismatchCount === String(targetMismatchCount) &&
          summary.dataset.batchFailedCount === String(targetFailedCount)
        );
      },
      [phase, total, completed, matchCount, mismatchCount, failedCount],
      timeout
    );
  }

  async function assertRequestBatchRow({
    method,
    path,
    expectedStatus,
    actualStatus,
    checkState,
    attemptCount = null,
    rerunOutcome = null,
    rerunOutcomeTone = null,
    timeout = 10000,
  }) {
    await waitForPageCondition(
      `assertRequestBatchRow(${method},${checkState})`,
      ([targetMethod, targetPath, targetExpectedStatus, targetActualStatus, targetCheckState, targetAttemptCount, targetRerunOutcome, targetRerunOutcomeTone]) => {
        const rows = Array.from(document.querySelectorAll("#requestBatchSummary [data-batch-method]"));
        return rows.some((row) => {
          const pathMatches = targetPath ? row.dataset.batchPath === targetPath : true;
          const attemptLabel = row.querySelector(".request-batch-summary__attempts");
          const attemptsMatch = targetAttemptCount
            ? (
              row.dataset.batchAttemptCount === targetAttemptCount &&
              attemptLabel &&
              (attemptLabel.textContent || "").includes(targetAttemptCount)
            )
            : true;
          const outcomeLabel = row.querySelector(".request-batch-summary__rerun-outcome");
          const outcomeMatches = targetRerunOutcome
            ? (
              row.dataset.batchRerunOutcome === targetRerunOutcome &&
              row.dataset.batchRerunOutcomeTone === targetRerunOutcomeTone &&
              outcomeLabel &&
              /Последний повтор|Last rerun/.test(outcomeLabel.textContent || "")
            )
            : true;
          return (
            row.dataset.batchMethod === targetMethod &&
            pathMatches &&
            row.dataset.batchExpectedStatus === targetExpectedStatus &&
            row.dataset.batchActualStatus === targetActualStatus &&
            row.dataset.batchCheck === targetCheckState &&
            attemptsMatch &&
            outcomeMatches
          );
        });
      },
      [
        method,
        path || "",
        expectedStatus,
        actualStatus,
        checkState,
        attemptCount === null ? "" : String(attemptCount),
        rerunOutcome || "",
        rerunOutcomeTone || "",
      ],
      timeout
    );
  }

  async function assertRequestBatchAttemptHistory({
    method,
    attemptCount,
    actualStatus,
    checkState,
    timeout = 10000,
  }) {
    const history = page.locator(`#requestBatchSummary [data-batch-method="${method}"] details.request-batch-summary__history`);
    await history.waitFor({ state: "attached", timeout });
    const isOpen = await history.evaluate((node) => node.open);
    if (!isOpen) {
      await history.locator("summary").click();
    }

    await waitForPageCondition(
      `assertRequestBatchAttemptHistory(${method},${attemptCount})`,
      ([targetMethod, targetAttemptCount, targetActualStatus, targetCheckState]) => {
        const rows = Array.from(document.querySelectorAll("#requestBatchSummary [data-batch-method]"));
        const row = rows.find((item) => item.dataset.batchMethod === targetMethod);
        const details = row?.querySelector("details.request-batch-summary__history");
        const items = Array.from(row?.querySelectorAll("[data-batch-attempt-index]") || []);
        const rowText = row?.innerText || "";

        return Boolean(
          row &&
          details &&
          details.open &&
          details.dataset.batchAttemptHistory === targetMethod &&
          details.dataset.batchAttemptHistoryCount === targetAttemptCount &&
          (rowText.includes("История попыток") || rowText.includes("Attempt history")) &&
          items.length === Number(targetAttemptCount) &&
          items.every((item) => (
            item.dataset.batchAttemptActualStatus === targetActualStatus &&
            item.dataset.batchAttemptCheck === targetCheckState
          ))
        );
      },
      [method, String(attemptCount), actualStatus, checkState],
      timeout
    );
  }

  async function assertRequestBatchAttemptHistoryState({
    method,
    attemptCount,
    open,
    autoOpen,
    timeout = 10000,
  }) {
    await waitForPageCondition(
      `assertRequestBatchAttemptHistoryState(${method},${attemptCount},${open})`,
      ([targetMethod, targetAttemptCount, targetOpen, targetAutoOpen]) => {
        const row = Array.from(document.querySelectorAll("#requestBatchSummary [data-batch-method]"))
          .find((item) => item.dataset.batchMethod === targetMethod);
        const details = row?.querySelector("details.request-batch-summary__history");
        const items = Array.from(row?.querySelectorAll("[data-batch-attempt-index]") || []);

        return Boolean(
          row &&
          details &&
          details.open === targetOpen &&
          details.dataset.batchAttemptHistory === targetMethod &&
          details.dataset.batchAttemptHistoryCount === String(targetAttemptCount) &&
          details.dataset.batchAttemptHistoryOpen === String(targetAutoOpen) &&
          items.length === Number(targetAttemptCount)
        );
      },
      [method, attemptCount, open, autoOpen],
      timeout
    );
  }

  async function injectRequestBatchMismatch({
    method,
    path,
    status,
    statusText,
    attemptCount,
    rerunOutcome,
    timeout = 10000,
  }) {
    await page.evaluate(([targetMethod, targetPath, targetStatus, targetStatusText]) => {
      if (
        typeof window.buildRequestExecutionResult !== "function" ||
        typeof window.updateRequestBatchResult !== "function"
      ) {
        throw new Error("Request batch helpers are unavailable");
      }

      const result = window.buildRequestExecutionResult(targetMethod, targetPath, {
        kind: "response",
        status: targetStatus,
        statusText: targetStatusText,
      });
      window.updateRequestBatchResult(targetMethod, targetPath, result);
    }, [method, path, status, statusText]);

    await assertRequestBatchRow({
      method,
      path,
      expectedStatus: "200 OK",
      actualStatus: `${status} ${statusText}`,
      checkState: "mismatch",
      attemptCount,
      rerunOutcome,
      rerunOutcomeTone: "danger",
      timeout,
    });
  }

  async function assertRequestPanelMethodOrder(expectedMethods, timeout = 10000) {
    await waitForPageCondition(
      "request panel method order",
      ([targetMethods]) => {
        const buttons = Array.from(document.querySelectorAll(".request-method-switch [data-request-method]"));
        return (
          buttons.length === targetMethods.length &&
          buttons.every((button, index) => {
            const method = button.dataset.requestMethod || "";
            const text = (button.textContent || "").trim();
            return method === targetMethods[index] && text === targetMethods[index];
          })
        );
      },
      [expectedMethods],
      timeout
    );
  }

  async function assertRequestBatchLegend({ matchText, issueText, label }, timeout = 10000) {
    await waitForPageCondition(
      "request batch legend",
      ([targetMatchText, targetIssueText, targetLabel]) => {
        const legend = document.getElementById("requestBatchLegend");
        const matchDot = legend?.querySelector(".request-batch-legend__dot--match");
        const issueDot = legend?.querySelector(".request-batch-legend__dot--issue");
        const content = legend?.innerText || "";
        return Boolean(
          legend &&
          matchDot &&
          issueDot &&
          legend.getAttribute("aria-label") === targetLabel &&
          content.includes(targetMatchText) &&
          content.includes(targetIssueText)
        );
      },
      [matchText, issueText, label],
      timeout
    );
  }

  async function runRequestPanelMethodScenario({
    method,
    initialPath = "/",
    expectedRequestPath,
    expectedPathInput,
    expectedStatus,
    responseIncludes = [],
    previewIncludes = [],
    timeout = 15000,
  }) {
    await page.locator("#pathInput").fill(initialPath);
    await page.locator(`.request-method-switch [data-request-method="${method}"]`).click();
    await waitForRequestPanelResponse(method, expectedStatus, expectedRequestPath, timeout);

    if (expectedPathInput) {
      await waitForValue("#pathInput", expectedPathInput, timeout);
    }

    const responseText = (await page.locator("#responseArea").innerText()).trim();
    for (const expectedText of responseIncludes) {
      if (!responseText.includes(expectedText)) {
        throw new Error(`Request panel ${method} response missing "${expectedText}": ${responseText}`);
      }
    }

    await waitForRequestPreview(method, expectedRequestPath, timeout);
    const previewText = (await page.locator("#requestPreviewArea").innerText()).trim();
    for (const expectedText of [`${method} ${expectedRequestPath} HTTP/1.1`, ...previewIncludes]) {
      if (!previewText.includes(expectedText)) {
        throw new Error(`Request panel ${method} preview missing "${expectedText}": ${previewText}`);
      }
    }

    await waitForLiveRegionText("responseAreaLive", `${method} ${expectedRequestPath} ${expectedStatus}`, timeout);

    return responseText;
  }

  async function assertRequestPanelScenarioMatrix() {
    const expectedMethods = [
      "GET",
      "HEAD",
      "POST",
      "PUT",
      "PATCH",
      "DELETE",
      "OPTIONS",
      "FETCH",
      "INFO",
      "PING",
      "NONE",
      "NOTE",
      "SMUGGLE",
    ];
    await assertRequestPanelMethodOrder(expectedMethods);
    await assertRequestBatchLegend({
      matchText: "Совпало",
      issueText: "Проблема",
      label: "Легенда статусов методов",
    });
    await assertRequestPreviewToggleState(false, false);
    await assertRequestPreviewModeState("raw");
    await assertResponseViewState("raw");
    await waitForPageCondition(
      "request batch export initially disabled",
      () => {
        const exportBtn = document.getElementById("requestBatchExportBtn");
        const clearBtn = document.getElementById("requestBatchClearBtn");
        return Boolean(exportBtn && exportBtn.disabled && clearBtn && clearBtn.disabled);
      },
      null,
      10000
    );
    await assertRequestBatchIssuesFilter({
      checked: false,
      filter: "all",
      visibleCount: 0,
      emptyText: "",
      timeout: 10000,
    });
    await page.locator("#requestPreviewToggle").check();
    await assertRequestPreviewToggleState(true, true);
    await assertRequestPreviewModeState("raw");
    await assertResponseViewState("raw");
    await waitForText(page.locator("#requestPreviewArea"), /Выберите метод|Choose a method/, 10000);
    await page.reload();
    await waitForSpaReady();
    await assertRequestPreviewToggleState(true, true);
    await assertRequestPreviewModeState("raw");
    await assertResponseViewState("raw");
    await waitForText(page.locator("#requestPreviewArea"), /Выберите метод|Choose a method/, 10000);
    await page.locator('[data-request-preview-mode="summary"]').click();
    await assertRequestPreviewModeState("summary");
    await assertResponseViewState("summary");
    await page.reload();
    await waitForSpaReady();
    await assertRequestPreviewToggleState(true, true);
    await assertRequestPreviewModeState("summary");
    await assertResponseViewState("summary");
    await page.locator("#pathInput").fill("/index.html");
    await page.locator('.request-method-switch [data-request-method="GET"]').click();
    await waitForRequestPanelResponse("GET", 200, "/index.html", 15000);
    await waitForRequestPreview("GET", "/index.html", 15000);
    await assertRequestPreviewSummary("GET", "/index.html", ["GET", "/index.html", "Host", "200 OK"], 15000);
    await assertResponseSummary("GET", "/index.html", ["GET", "/index.html", "200 OK"], 15000);
    await page.locator("#requestPreviewCopyBtn").click();
    await assertClipboardSnapshot("request", ["GET /index.html HTTP/1.1", "Host:"], 15000);
    await page.locator("#responseCopyBtn").click();
    await assertClipboardSnapshot("response", ["GET /index.html", "200 OK", "--- Заголовки ---"], 15000);
    await assertRequestPreviewComparison({
      method: "GET",
      path: "/index.html",
      expectedStatus: "200 OK",
      actualStatus: "200 OK",
      checkState: "match",
      timeout: 15000,
    });
    await page.locator('[data-request-preview-mode="raw"]').click();
    await assertRequestPreviewModeState("raw");
    await assertResponseViewState("raw");
    await assertResponseRaw("GET", "/index.html", ["GET /index.html", "200 OK"], 15000);
    await page.locator('[data-request-preview-mode="summary"]').click();
    await assertRequestPreviewModeState("summary");
    await assertResponseViewState("summary");
    await assertResponseSummary("GET", "/index.html", ["GET", "/index.html", "200 OK"], 15000);
    await page.locator("#pathInput").fill("/ignored-post");
    await page.locator('.request-method-switch [data-request-method="POST"]').click();
    await waitForRequestPanelResponse("POST", 201, "/", 15000);
    await waitForRequestPreview("POST", "/", 15000);
    await waitForValue("#pathInput", "/uploads/request-panel-post.txt", 15000);
    await assertRequestPreviewSummary("POST", "/", ["POST", "/", "201 Created"], 15000);
    await assertRequestPreviewComparison({
      method: "POST",
      path: "/",
      expectedStatus: "201 Created",
      actualStatus: "201 Created",
      checkState: "match",
      timeout: 15000,
    });
    const missingPath = "/missing-browser-smoke.txt";
    await page.locator("#pathInput").fill(missingPath);
    await page.locator('.request-method-switch [data-request-method="GET"]').click();
    await waitForRequestPanelResponse("GET", 404, missingPath, 15000);
    await waitForRequestPreview("GET", missingPath, 15000);
    await assertRequestPreviewSummary("GET", missingPath, ["GET", missingPath, "404 Not Found"], 15000);
    await assertRequestPreviewComparison({
      method: "GET",
      path: missingPath,
      expectedStatus: "200 OK",
      actualStatus: "404 Not Found",
      checkState: "mismatch",
      timeout: 15000,
    });
    await page.locator("#requestRunAllBtn").click();
    await waitForRequestBatchSummary({
      phase: "complete",
      total: 13,
      completed: 13,
      matchCount: 13,
      mismatchCount: 0,
      failedCount: 0,
      timeout: 60000,
    });
    await assertRequestBatchRow({
      method: "POST",
      path: "/",
      expectedStatus: "201 Created",
      actualStatus: "201 Created",
      checkState: "match",
      timeout: 15000,
    });
    await assertRequestBatchRow({
      method: "OPTIONS",
      path: "/",
      expectedStatus: "204 No Content",
      actualStatus: "204 No Content",
      checkState: "match",
      timeout: 15000,
    });
    await assertRequestMethodButtonBatchState({
      method: "GET",
      checkState: "match",
      expectedStatus: "200 OK",
      actualStatus: "200 OK",
      timeout: 15000,
    });
    await assertRequestMethodButtonBatchState({
      method: "POST",
      checkState: "match",
      expectedStatus: "201 Created",
      actualStatus: "201 Created",
      timeout: 15000,
    });
    await assertRequestMethodButtonBatchState({
      method: "OPTIONS",
      checkState: "match",
      expectedStatus: "204 No Content",
      actualStatus: "204 No Content",
      timeout: 15000,
    });
    await assertRequestBatchExport({
      phase: "complete",
      total: 13,
      completed: 13,
      matchCount: 13,
      mismatchCount: 0,
      failedCount: 0,
      expectedMethods: ["GET", "POST", "OPTIONS", "SMUGGLE"],
      expectedAttemptCounts: {
        GET: 1,
        OPTIONS: 1,
      },
      timeout: 15000,
    });
    await assertRequestBatchRerunIssuesButtonState({
      disabled: true,
      issueCount: 0,
      timeout: 15000,
    });
    await injectRequestBatchMismatch({
      method: "GET",
      path: "/index.html",
      status: 404,
      statusText: "Not Found",
      attemptCount: 2,
      rerunOutcome: "regressed",
      timeout: 15000,
    });
    await waitForRequestBatchSummary({
      phase: "complete",
      total: 13,
      completed: 13,
      matchCount: 12,
      mismatchCount: 1,
      failedCount: 0,
      timeout: 15000,
    });
    await assertRequestBatchAttemptHistoryState({
      method: "GET",
      attemptCount: 2,
      open: true,
      autoOpen: true,
      timeout: 15000,
    });
    await injectRequestBatchMismatch({
      method: "GET",
      path: "/index.html",
      status: 500,
      statusText: "Internal Server Error",
      attemptCount: 3,
      rerunOutcome: "still-failing",
      timeout: 15000,
    });
    await waitForRequestBatchSummary({
      phase: "complete",
      total: 13,
      completed: 13,
      matchCount: 12,
      mismatchCount: 1,
      failedCount: 0,
      timeout: 15000,
    });
    await assertRequestBatchAttemptHistoryState({
      method: "GET",
      attemptCount: 3,
      open: true,
      autoOpen: true,
      timeout: 15000,
    });
    await assertRequestMethodButtonBatchState({
      method: "GET",
      checkState: "mismatch",
      expectedStatus: "200 OK",
      actualStatus: "500 Internal Server Error",
      timeout: 15000,
    });
    await assertRequestBatchRerunIssuesButtonState({
      disabled: false,
      issueCount: 1,
      timeout: 15000,
    });
    await page.locator("#requestBatchRerunIssuesBtn").click();
    await waitForRequestPanelResponse("GET", 200, "/index.html", 15000);
    await waitForValue("#pathInput", "/index.html", 15000);
    await waitForRequestBatchSummary({
      phase: "complete",
      total: 13,
      completed: 13,
      matchCount: 13,
      mismatchCount: 0,
      failedCount: 0,
      timeout: 15000,
    });
    await assertRequestBatchRow({
      method: "GET",
      path: "/index.html",
      expectedStatus: "200 OK",
      actualStatus: "200 OK",
      checkState: "match",
      attemptCount: 4,
      rerunOutcome: "fixed",
      rerunOutcomeTone: "success",
      timeout: 15000,
    });
    await assertRequestBatchAttemptHistoryState({
      method: "GET",
      attemptCount: 4,
      open: false,
      autoOpen: false,
      timeout: 15000,
    });
    await assertRequestMethodButtonBatchState({
      method: "GET",
      checkState: "match",
      expectedStatus: "200 OK",
      actualStatus: "200 OK",
      timeout: 15000,
    });
    await assertRequestBatchRerunIssuesButtonState({
      disabled: true,
      issueCount: 0,
      timeout: 15000,
    });
    await page.locator("#requestBatchIssuesOnlyToggle").check();
    await assertRequestBatchIssuesFilter({
      checked: true,
      filter: "issues",
      visibleCount: 0,
      emptyText: "Расхождений и ошибок нет.",
      timeout: 15000,
    });
    await page.locator("#requestBatchIssuesOnlyToggle").uncheck();
    await assertRequestBatchIssuesFilter({
      checked: false,
      filter: "all",
      visibleCount: 13,
      emptyText: "",
      timeout: 15000,
    });
    await page.locator('#requestBatchSummary [data-batch-rerun-method="OPTIONS"]').click();
    await waitForRequestPanelResponse("OPTIONS", 204, "/", 15000);
    await waitForValue("#pathInput", "/", 15000);
    await assertRequestBatchRow({
      method: "OPTIONS",
      path: "/",
      expectedStatus: "204 No Content",
      actualStatus: "204 No Content",
      checkState: "match",
      attemptCount: 2,
      rerunOutcome: "still-ok",
      rerunOutcomeTone: "success",
      timeout: 15000,
    });
    await assertRequestBatchAttemptHistory({
      method: "OPTIONS",
      attemptCount: 2,
      actualStatus: "204 No Content",
      checkState: "match",
      timeout: 15000,
    });
    await assertRequestMethodButtonBatchState({
      method: "OPTIONS",
      checkState: "match",
      expectedStatus: "204 No Content",
      actualStatus: "204 No Content",
      timeout: 15000,
    });
    await assertRequestBatchExport({
      phase: "complete",
      total: 13,
      completed: 13,
      matchCount: 13,
      mismatchCount: 0,
      failedCount: 0,
      expectedMethods: ["GET", "OPTIONS"],
      expectedAttemptCounts: {
        GET: 4,
        OPTIONS: 2,
      },
      timeout: 15000,
    });
    await page.locator("#requestBatchClearBtn").click();
    await assertRequestBatchCleared(15000);
    await assertRequestBatchIssuesFilter({
      checked: false,
      filter: "all",
      visibleCount: 0,
      emptyText: "",
      timeout: 15000,
    });
    await page.locator('[data-request-preview-mode="raw"]').click();
    await assertRequestPreviewModeState("raw");
    await assertResponseViewState("raw");
    await page.locator("#requestPreviewToggle").uncheck();
    await assertRequestPreviewToggleState(false, false);
    await page.reload();
    await waitForSpaReady();
    await assertRequestPreviewToggleState(false, false);
    await assertRequestPreviewModeState("raw");
    await assertResponseViewState("raw");
    await page.locator("#requestPreviewToggle").check();
    await assertRequestPreviewToggleState(true, true);
    await assertRequestPreviewModeState("raw");
    await assertResponseViewState("raw");

    await runRequestPanelMethodScenario({
      method: "GET",
      initialPath: "/index.html",
      expectedRequestPath: "/index.html",
      expectedPathInput: "/index.html",
      expectedStatus: 200,
      responseIncludes: ["GET /index.html"],
      previewIncludes: ["Host:"],
    });

    await runRequestPanelMethodScenario({
      method: "HEAD",
      initialPath: "/index.html",
      expectedRequestPath: "/index.html",
      expectedPathInput: "/index.html",
      expectedStatus: 200,
      responseIncludes: ["HEAD /index.html"],
      previewIncludes: ["Host:"],
    });

    await runRequestPanelMethodScenario({
      method: "POST",
      initialPath: "/ignored-post",
      expectedRequestPath: "/",
      expectedPathInput: "/uploads/request-panel-post.txt",
      expectedStatus: 201,
      responseIncludes: ['"path": "/uploads/request-panel-post.txt"'],
      previewIncludes: [
        "X-File-Name: request-panel-post.txt",
        "Content-Type: text/plain; charset=utf-8",
        "Content-Length:",
        "request-panel demo via POST",
      ],
    });

    await runRequestPanelMethodScenario({
      method: "PUT",
      initialPath: "/ignored-put",
      expectedRequestPath: "/",
      expectedPathInput: "/uploads/request-panel-put.txt",
      expectedStatus: 201,
      responseIncludes: ['"path": "/uploads/request-panel-put.txt"'],
      previewIncludes: [
        "X-File-Name: request-panel-put.txt",
        "Content-Type: text/plain; charset=utf-8",
        "Content-Length:",
        "request-panel demo via PUT",
      ],
    });

    await runRequestPanelMethodScenario({
      method: "PATCH",
      initialPath: "/ignored-patch",
      expectedRequestPath: "/",
      expectedPathInput: "/uploads/request-panel-patch.txt",
      expectedStatus: 201,
      responseIncludes: ['"path": "/uploads/request-panel-patch.txt"'],
      previewIncludes: [
        "X-File-Name: request-panel-patch.txt",
        "Content-Type: text/plain; charset=utf-8",
        "Content-Length:",
        "request-panel demo via PATCH",
      ],
    });

    await runRequestPanelMethodScenario({
      method: "DELETE",
      initialPath: "/ignored-delete",
      expectedRequestPath: "/uploads/request-panel-delete.txt",
      expectedPathInput: "/uploads/request-panel-delete.txt",
      expectedStatus: 200,
      responseIncludes: ['"deleted": "request-panel-delete.txt"'],
    });

    await runRequestPanelMethodScenario({
      method: "OPTIONS",
      initialPath: "/ignored-options",
      expectedRequestPath: "/",
      expectedPathInput: "/",
      expectedStatus: 204,
      responseIncludes: ["OPTIONS /"],
      previewIncludes: ["Access-Control-Request-Method: GET"],
    });

    await runRequestPanelMethodScenario({
      method: "INFO",
      initialPath: "/",
      expectedRequestPath: "/",
      expectedPathInput: "/",
      expectedStatus: 200,
      responseIncludes: ['"is_directory": true'],
      previewIncludes: ["Host:"],
    });

    await runRequestPanelMethodScenario({
      method: "PING",
      initialPath: "/ignored-ping",
      expectedRequestPath: "/",
      expectedPathInput: "/",
      expectedStatus: 200,
      responseIncludes: ['"status": "pong"'],
      previewIncludes: ["Host:"],
    });

    await runRequestPanelMethodScenario({
      method: "NONE",
      initialPath: "/ignored-none",
      expectedRequestPath: "/",
      expectedPathInput: "/uploads/request-panel-none.txt",
      expectedStatus: 201,
      responseIncludes: ['"path": "/uploads/request-panel-none.txt"'],
      previewIncludes: [
        "X-File-Name: request-panel-none.txt",
        "Content-Type: text/plain; charset=utf-8",
        "Content-Length:",
        "request-panel demo via NONE",
      ],
    });

    await runRequestPanelMethodScenario({
      method: "NOTE",
      initialPath: "/ignored-note",
      expectedRequestPath: "/notes/key",
      expectedPathInput: "/notes/key",
      expectedStatus: 200,
      responseIncludes: ['"hasEcdh":'],
      previewIncludes: ["Host:"],
    });

    await runRequestPanelMethodScenario({
      method: "SMUGGLE",
      initialPath: "/ignored-smuggle",
      expectedRequestPath: "/uploads/request-panel-smuggle.txt",
      expectedPathInput: "/uploads/request-panel-smuggle.txt",
      expectedStatus: 200,
      responseIncludes: ['"url": "/uploads/smuggle_'],
    });

    const fetchPath = "/uploads/request-panel-fetch.txt";
    await runRequestPanelMethodScenario({
      method: "FETCH",
      initialPath: "/ignored-fetch",
      expectedRequestPath: fetchPath,
      expectedPathInput: fetchPath,
      expectedStatus: 200,
      responseIncludes: ["FETCH /uploads/request-panel-fetch.txt"],
    });

    const downloadButton = page.locator("#responseArea [data-download-path]");
    await downloadButton.waitFor({ state: "attached", timeout: 10000 });

    const fetchFileName = "request-panel-fetch.txt";
    const downloadPromise = page.waitForEvent("download");
    await downloadButton.click();
    await waitForPageCondition(
      `request-panel download progress mounted (${fetchFileName})`,
      ([targetName]) => {
        const progressArea = document.getElementById("downloadProgressArea");
        const progressText = document.getElementById("dlProgressText");
        return Boolean(progressArea && progressText && progressArea.innerText.includes(targetName));
      },
      [fetchFileName],
      10000
    );
    const download = await downloadPromise;
    const suggestedFilename = download.suggestedFilename();
    if (suggestedFilename !== fetchFileName) {
      throw new Error(`Request-panel FETCH download filename mismatch: ${suggestedFilename}`);
    }

    return fetchPath;
  }

  async function fetchViaRequestPanelAndAssert() {
    return assertRequestPanelScenarioMatrix();
  }

  function getServerFileAction(name, action) {
    const encodedPath = encodeURIComponent(`/uploads/${name}`);
    return page.locator(`#serverFiles [data-file-action="${action}"][data-path="${encodedPath}"]`).first();
  }

  async function fetchViaServerFilesAndAssert(name) {
    const actionButton = getServerFileAction(name, "download");
    await actionButton.waitFor({ state: "visible", timeout: 10000 });

    const downloadPromise = page.waitForEvent("download");
    await actionButton.click();
    await waitForPageCondition(
      `server-files download progress mounted (${name})`,
      ([targetName]) => {
        const progressArea = document.getElementById("downloadProgressArea");
        const progressText = document.getElementById("dlProgressText");
        return Boolean(progressArea && progressText && progressArea.innerText.includes(targetName));
      },
      [name],
      10000
    );
    const download = await downloadPromise;
    const suggestedFilename = download.suggestedFilename();
    if (suggestedFilename !== name) {
      throw new Error(`Server-files FETCH download filename mismatch: ${suggestedFilename}`);
    }
  }

  async function assertFileActionAccessibleNames(name) {
    const encodedPath = encodeURIComponent(`/uploads/${name}`);
    const actions = [
      { action: "download", prefix: /Download files|Скачивание файлов/i },
      { action: "info", prefix: /File metadata|Метаданные файла/i },
      { action: "smuggle", prefix: /SMUGGLE|HTML Smuggling/i },
      { action: "delete", prefix: /Delete|Удалить/i },
    ];

    for (const { action, prefix } of actions) {
      const button = page.locator(`#serverFiles [data-file-action="${action}"][data-path="${encodedPath}"]`).first();
      await button.waitFor({ state: "visible", timeout: 10000 });
      const ariaLabel = (await button.getAttribute("aria-label")) || "";
      if (!prefix.test(ariaLabel) || !ariaLabel.includes(name)) {
        throw new Error(`Unexpected accessible name for ${action}: ${ariaLabel}`);
      }
    }
  }

  async function smuggleViaServerFilesAndAssert(name) {
    const actionButton = getServerFileAction(name, "smuggle");
    await actionButton.waitFor({ state: "visible", timeout: 10000 });
    await actionButton.click();

    const modal = page.locator("#smuggleModal");
    await modal.waitFor({ state: "attached", timeout: 10000 });
    await page.locator('#smuggleModal [role="dialog"]').waitFor({ state: "visible", timeout: 10000 });
    await page.locator("#smuggleSubmitBtn").waitFor({ state: "visible", timeout: 10000 });
    await page.locator("#smuggleCancelBtn").waitFor({ state: "visible", timeout: 10000 });
    await page.locator("#smuggleEncrypt").waitFor({ state: "attached", timeout: 10000 });

    const popupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
    await page.locator("#smuggleSubmitBtn").click();
    await modal.waitFor({ state: "detached", timeout: 10000 });

    await waitForText(page.locator("#filesResponseArea"), `SMUGGLE /uploads/${name}`, 10000);
    await waitForText(page.locator("#filesResponseArea"), /HTML сгенерирован|HTML generated/, 10000);
    await waitForText(page.locator("#filesResponseArea"), "URL:", 10000);

    const popup = await popupPromise;
    const popupUrl = popup ? popup.url() : "";
    if (popup) {
      await popup.waitForLoadState("domcontentloaded");
      await popup.close();
    }
    return popupUrl;
  }

  async function assertSmuggleDialogKeyboardContract(name) {
    const encodedPath = encodeURIComponent(`/uploads/${name}`);
    const actionButton = getServerFileAction(name, "smuggle");
    await actionButton.waitFor({ state: "visible", timeout: 10000 });
    await actionButton.focus();

    await page.keyboard.press("Enter");
    const modal = page.locator("#smuggleModal");
    await modal.waitFor({ state: "attached", timeout: 10000 });
    await page.locator('#smuggleModal [role="dialog"]').waitFor({ state: "visible", timeout: 10000 });

    await waitForPageCondition(
      `smuggle dialog initial focus (${name})`,
      () => document.activeElement?.id === "smuggleSubmitBtn",
      null,
      10000
    );

    await page.keyboard.press("Tab");
    await waitForPageCondition(
      `smuggle dialog tab to cancel (${name})`,
      () => document.activeElement?.id === "smuggleCancelBtn",
      null,
      10000
    );

    await page.keyboard.press("Tab");
    await waitForPageCondition(
      `smuggle dialog wrap to checkbox (${name})`,
      () => document.activeElement?.id === "smuggleEncrypt",
      null,
      10000
    );

    await page.keyboard.press("Shift+Tab");
    await waitForPageCondition(
      `smuggle dialog reverse wrap to cancel (${name})`,
      () => document.activeElement?.id === "smuggleCancelBtn",
      null,
      10000
    );

    await page.keyboard.press("Escape");
    await page.locator("#smuggleModal").waitFor({ state: "detached", timeout: 10000 });

    await waitForPageCondition(
      `smuggle dialog focus restored (${name})`,
      ([targetPath]) => {
        const active = document.activeElement;
        return Boolean(
          active &&
          active.getAttribute("data-file-action") === "smuggle" &&
          active.getAttribute("data-path") === targetPath
        );
      },
      [encodedPath],
      10000
    );
  }

  async function infoViaServerFilesAndAssert(name) {
    const requestPath = `/uploads/${name}`;
    const actionButton = getServerFileAction(name, "info");
    await actionButton.waitFor({ state: "visible", timeout: 10000 });
    await actionButton.click();

    await waitForValue("#browsePathInput", requestPath, 10000);
    await waitForText(page.locator("#filesResponseArea"), `INFO ${requestPath}`, 10000);
    await waitForText(page.locator("#filesResponseArea"), "200 OK", 10000);

    return requestPath;
  }

  async function deleteViaServerFilesAndAssert(name) {
    const encodedPath = encodeURIComponent(`/uploads/${name}`);
    const actionButton = getServerFileAction(name, "delete");
    await actionButton.waitFor({ state: "visible", timeout: 10000 });

    await actionButton.click();
    await confirmAppDialog(name, 10000);

    await waitForPageCondition(
      `deleted file action removed from serverFiles (${name})`,
      ([targetPath]) => {
        return !document.querySelector(`#serverFiles [data-path="${targetPath}"]`);
      },
      [encodedPath],
      10000
    );
    await waitForPageCondition(
      `focus anchored after delete (${name})`,
      () => document.activeElement?.id === "browsePathInput",
      null,
      10000
    );
  }

  async function assertDeleteDialogKeyboardContract(name) {
    const actionButton = getServerFileAction(name, "delete");
    await actionButton.waitFor({ state: "visible", timeout: 10000 });
    await actionButton.focus();

    await page.keyboard.press("Enter");
    const dialog = page.locator('#appDialog [role="alertdialog"]');
    await dialog.waitFor({ state: "visible", timeout: 10000 });

    await waitForPageCondition(
      `delete dialog initial focus (${name})`,
      () => document.activeElement?.getAttribute("data-dialog-action") === "cancel",
      null,
      10000
    );

    await page.keyboard.press("Shift+Tab");
    await waitForPageCondition(
      `delete dialog reverse tab trap (${name})`,
      () => document.activeElement?.getAttribute("data-dialog-action") === "confirm",
      null,
      10000
    );

    await page.keyboard.press("Tab");
    await waitForPageCondition(
      `delete dialog forward tab trap (${name})`,
      () => document.activeElement?.getAttribute("data-dialog-action") === "cancel",
      null,
      10000
    );

    await page.keyboard.press("Escape");
    await page.locator("#appDialog").waitFor({ state: "detached", timeout: 10000 });

    const encodedPath = encodeURIComponent(`/uploads/${name}`);
    await waitForPageCondition(
      `delete dialog focus restored (${name})`,
      ([targetPath]) => {
        const active = document.activeElement;
        return Boolean(
          active &&
          active.getAttribute("data-file-action") === "delete" &&
          active.getAttribute("data-path") === targetPath
        );
      },
      [encodedPath],
      10000
    );
  }

  async function prepareOpsecTransportScenario(initialTransport) {
    await page.locator("#tab-opsec").click();
    await waitForTabState("opsec", { focused: true });

    await page.evaluate(() => {
      if (typeof setOpsecFile === "function") {
        setOpsecFile(null);
      }
      const input = document.getElementById("opsecFileInput");
      if (input) {
        input.value = "";
      }
    });
    await waitForPageCondition(
      "opsec selection reset",
      () => {
        const uploadBtn = document.getElementById("opsecUploadBtn");
        const warning = document.getElementById("opsecTransportWarning");
        const selectionState = document.getElementById("opsecSelectionState");
        const selectionReset = Boolean(
          selectionState &&
          (
            selectionState.hidden === true ||
            /No file selected(?: yet)?|Файл(?: пока)? не выбран/.test(selectionState.innerText)
          )
        );
        return Boolean(
          uploadBtn &&
          uploadBtn.disabled &&
          warning &&
          warning.hidden === true &&
          selectionReset
        );
      },
      null,
      10000
    );

    await switchLanguage("en");
    await page.locator(`input[name="opsecTransport"][value="${initialTransport}"]`).check();
    await waitForPageCondition(
      `opsec transport preselected ${initialTransport}`,
      ([targetTransport]) => document.querySelector('input[name="opsecTransport"]:checked')?.value === targetTransport,
      [initialTransport],
      10000
    );
  }

  async function assertOpsecAutoSwitch({
    fixturePath,
    initialTransport,
    expectedTransport,
    expectedWarningFromKey,
    expectedWarningToKey,
    expectedWarningTokensRu = null,
  }) {
    const opsecFixtureName = fixturePath.split(/[\\/]/).pop();

    await prepareOpsecTransportScenario(initialTransport);

    await page.locator("#opsecFileInput").setInputFiles(fixturePath);

    await waitForLiveRegionText("opsecResponseAreaLive", `File selected: ${opsecFixtureName}`, 10000);
    await waitForPageCondition(
      `opsec auto-switch to ${expectedTransport}`,
      ([expectedName, targetTransport, fromKey, toKey]) => {
        const selectedTransport = document.querySelector('input[name="opsecTransport"]:checked');
        const warning = document.getElementById("opsecTransportWarning");
        const selectionState = document.getElementById("opsecSelectionState");

        return Boolean(
          selectedTransport &&
          selectedTransport.value === targetTransport &&
          warning &&
          warning.hidden === false &&
          warning.dataset.fromKey === fromKey &&
          warning.dataset.toKey === toKey &&
          selectionState &&
          selectionState.innerText.includes(expectedName)
        );
      },
      [opsecFixtureName, expectedTransport, expectedWarningFromKey, expectedWarningToKey],
      10000
    );

    const warningTextEn = await page.locator("#opsecTransportWarning").textContent() || "";

    const selectedTransport = await page.locator('input[name="opsecTransport"]:checked').getAttribute("value") || "";
    const result = {
      fixtureName: opsecFixtureName,
      selectedTransport,
      warningTextEn: warningTextEn.trim(),
    };

    if (!expectedWarningTokensRu) {
      return result;
    }

    await switchLanguage("ru");
    await waitForPageCondition(
      `opsec auto-switch warning translated to ru (${expectedTransport})`,
      ([warningTokens]) => {
        const warning = document.getElementById("opsecTransportWarning");
        const warningText = warning?.textContent?.trim() || "";
        return Boolean(
          warning &&
          warning.hidden === false &&
          warningText.startsWith("Транспорт переключён на") &&
          warningTokens.every((token) => warningText.includes(token))
        );
      },
      [expectedWarningTokensRu],
      10000
    );

    const warningTextRu = await page.locator("#opsecTransportWarning").textContent() || "";

    return {
      ...result,
      warningTextRu: warningTextRu.trim(),
    };
  }

  async function assertOpsecBoundaryNoSwitch({
    fixturePath,
    initialTransport,
  }) {
    const opsecFixtureName = fixturePath.split(/[\\/]/).pop();

    await prepareOpsecTransportScenario(initialTransport);
    await page.locator("#opsecFileInput").setInputFiles(fixturePath);

    await waitForLiveRegionText("opsecResponseAreaLive", `File selected: ${opsecFixtureName}`, 10000);
    await waitForPageCondition(
      `opsec boundary no switch (${initialTransport})`,
      ([expectedName, targetTransport]) => {
        const selectedTransport = document.querySelector('input[name="opsecTransport"]:checked');
        const warning = document.getElementById("opsecTransportWarning");
        const selectionState = document.getElementById("opsecSelectionState");

        return Boolean(
          selectedTransport &&
          selectedTransport.value === targetTransport &&
          warning &&
          warning.hidden === true &&
          !warning.dataset.fromKey &&
          !warning.dataset.toKey &&
          selectionState &&
          selectionState.innerText.includes(expectedName)
        );
      },
      [opsecFixtureName, initialTransport],
      10000
    );

    const selectedTransport = await page.locator('input[name="opsecTransport"]:checked').getAttribute("value") || "";

    return {
      fixtureName: opsecFixtureName,
      selectedTransport,
    };
  }

  async function createAutosavedNote(title, text) {
    await page.getByRole("button", { name: /Новая|New/ }).click();
    await page.locator("#notepadTitleInput").fill(title);
    await page.locator("#notepadTextarea").fill(text);
    try {
      await waitForText(page.locator("#notepadNoteList"), title, 15000);
      await waitForText(page.locator("#notepadSaveIndicator"), /Сохранено|Saved/, 15000);
    } catch (error) {
      const indicator = (await page.locator("#notepadSaveIndicator").textContent() || "").trim();
      throw new Error(`createAutosavedNote(${title}) failed: indicator=${indicator}; ${error.message}`);
    }
  }

  async function clickNoteByTitle(title) {
    await page.locator(".note-item", { hasText: title }).click();
    await waitForValue("#notepadTitleInput", title);
  }

  async function clearNotesViaUiAndAssert(uploadPathToPreserve) {
    const uploadNameToPreserve = uploadPathToPreserve.split("/").pop();

    await page.locator("#notepadClearBtn").click();
    await confirmAppDialog(/notes\//, 10000);
    await waitForPageCondition(
      "notepad notes cleared",
      () => {
        const titleInput = document.getElementById("notepadTitleInput");
        const textarea = document.getElementById("notepadTextarea");
        const deleteBtn = document.getElementById("notepadDeleteBtn");
        const noteList = document.getElementById("notepadNoteList");
        const indicator = document.getElementById("notepadSaveIndicator");
        return Boolean(
          titleInput &&
          textarea &&
          deleteBtn &&
          noteList &&
          indicator &&
          titleInput.value === "" &&
          textarea.value === "" &&
          deleteBtn.disabled &&
          /Нет заметок|No notes/.test(noteList.innerText) &&
          /Заметки очищены|Notes cleared/.test(indicator.innerText)
        );
      },
      null,
      15000
    );

    await browseUploadsAndAssert(uploadNameToPreserve);
    return uploadPathToPreserve;
  }

  async function deleteSelectedUploadViaUiAndAssert(path) {
    const name = path.split("/").pop();
    const encodedPath = encodeURIComponent(path);

    await browseUploadsAndAssert(name);
    await page.locator(`#serverFiles [data-file-select][data-path="${encodedPath}"]`).check();
    await page.locator("#deleteSelectedUploadsBtn").click();
    await confirmAppDialog(path, 10000);
    await waitForPageCondition(
      `selected upload deleted (${name})`,
      ([targetPath]) => !document.querySelector(`#serverFiles [data-path="${targetPath}"]`),
      [encodedPath],
      15000
    );
  }

  async function deleteSelectedNoteViaUiAndAssert(deleteTitle, keepTitle) {
    await page.locator(".note-row", { hasText: deleteTitle }).locator("[data-note-select]").check();
    await page.locator("#notepadDeleteSelectedBtn").click();
    await confirmAppDialog(deleteTitle, 10000);
    await waitForPageCondition(
      `selected note deleted (${deleteTitle})`,
      ([removedTitle, remainingTitle]) => {
        const noteList = document.getElementById("notepadNoteList");
        const titleInput = document.getElementById("notepadTitleInput");
        const textarea = document.getElementById("notepadTextarea");
        return Boolean(
          noteList &&
          titleInput &&
          textarea &&
          !noteList.innerText.includes(removedTitle) &&
          noteList.innerText.includes(remainingTitle) &&
          titleInput.value === "" &&
          textarea.value === ""
        );
      },
      [deleteTitle, keepTitle],
      15000
    );
  }

  async function loadNoteByKeyboard(title) {
    await page.locator("#notepadRefreshBtn").focus();
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Tab");
      const focused = await page.evaluate(([targetTitle]) => {
        const active = document.activeElement;
        return Boolean(
          active &&
          active.classList &&
          active.classList.contains("note-item") &&
          active.innerText.includes(targetTitle)
        );
      }, [title]);
      if (focused) {
        break;
      }
    }
    await waitForPageCondition(
      `note item focused (${title})`,
      ([targetTitle]) => {
        const active = document.activeElement;
        return Boolean(
          active &&
          active.classList &&
          active.classList.contains("note-item") &&
          active.textContent &&
          active.textContent.includes(targetTitle)
        );
      },
      [title],
      10000
    );
    await page.keyboard.press("Enter");
    await waitForValue("#notepadTitleInput", title);
  }

  async function assertMobileLayoutSnapshot(timeout = 10000) {
    const currentUrl = page.url();
    const rootUrl = currentUrl.replace(/^(https?:\/\/[^/]+).*/, "$1/");
    await page.goto(rootUrl, { waitUntil: "domcontentloaded" });
    await waitForSpaReady();
    await page.setViewportSize({ width: 390, height: 844 });

    await waitForPageCondition(
      "mobile layout snapshot",
      () => {
        const doc = document.documentElement;
        const requestSwitch = document.querySelector(".request-method-switch");
        const toolTabs = document.querySelector(".tool-tabs");
        const requestPanel = document.querySelector(".request-panel");
        const statusChip = document.querySelector(".status-chip");
        const liveStatusFull = document.querySelector(".status-chip--live .status-chip__label--full");
        const liveStatusCompact = document.querySelector(".status-chip--live .status-chip__label--compact");
        const heroResponse = document.querySelector(".response-area--hero");

        if (
          !requestSwitch ||
          !toolTabs ||
          !requestPanel ||
          !statusChip ||
          !liveStatusFull ||
          !liveStatusCompact ||
          !heroResponse
        ) {
          return false;
        }

        const countColumns = (trackList) => {
          const normalized = (trackList || "").trim();
          return normalized && normalized !== "none" ? normalized.split(/\s+/).length : 0;
        };

        const requestSwitchStyles = window.getComputedStyle(requestSwitch);
        const toolTabsStyles = window.getComputedStyle(toolTabs);
        const requestPanelStyles = window.getComputedStyle(requestPanel);
        const statusChipStyles = window.getComputedStyle(statusChip);
        const liveStatusFullStyles = window.getComputedStyle(liveStatusFull);
        const liveStatusCompactStyles = window.getComputedStyle(liveStatusCompact);
        const heroResponseStyles = window.getComputedStyle(heroResponse);

        return (
          doc.scrollWidth <= window.innerWidth + 1 &&
          countColumns(requestSwitchStyles.gridTemplateColumns) === 2 &&
          countColumns(toolTabsStyles.gridTemplateColumns) === 2 &&
          parseFloat(requestPanelStyles.paddingTop) <= 16.5 &&
          parseFloat(statusChipStyles.minHeight) <= 30.5 &&
          liveStatusFullStyles.display === "none" &&
          liveStatusCompactStyles.display !== "none" &&
          parseFloat(heroResponseStyles.minHeight) <= 220.5
        );
      },
      null,
      timeout
    );

    const snapshot = await page.evaluate(() => {
      const doc = document.documentElement;
      const requestSwitch = document.querySelector(".request-method-switch");
      const toolTabs = document.querySelector(".tool-tabs");
      const requestPanel = document.querySelector(".request-panel");
      const statusChip = document.querySelector(".status-chip");
      const liveStatusFull = document.querySelector(".status-chip--live .status-chip__label--full");
      const liveStatusCompact = document.querySelector(".status-chip--live .status-chip__label--compact");
      const heroResponse = document.querySelector(".response-area--hero");

      const countColumns = (trackList) => {
        const normalized = (trackList || "").trim();
        return normalized && normalized !== "none" ? normalized.split(/\s+/).length : 0;
      };

      const requestSwitchStyles = window.getComputedStyle(requestSwitch);
      const toolTabsStyles = window.getComputedStyle(toolTabs);
      const requestPanelStyles = window.getComputedStyle(requestPanel);
      const statusChipStyles = window.getComputedStyle(statusChip);
      const liveStatusFullStyles = window.getComputedStyle(liveStatusFull);
      const liveStatusCompactStyles = window.getComputedStyle(liveStatusCompact);
      const heroResponseStyles = window.getComputedStyle(heroResponse);

      return {
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        scrollWidth: doc.scrollWidth,
        requestMethodColumns: countColumns(requestSwitchStyles.gridTemplateColumns),
        toolTabColumns: countColumns(toolTabsStyles.gridTemplateColumns),
        requestPanelPaddingTop: parseFloat(requestPanelStyles.paddingTop),
        statusChipMinHeight: parseFloat(statusChipStyles.minHeight),
        liveStatusFullDisplay: liveStatusFullStyles.display,
        liveStatusCompactDisplay: liveStatusCompactStyles.display,
        liveStatusCompactText: (liveStatusCompact.textContent || "").trim(),
        heroResponseMinHeight: parseFloat(heroResponseStyles.minHeight),
      };
    });

    await page.setViewportSize({ width: 1440, height: 1024 });
    return snapshot;
  }

  async function runHappyPath() {
    await assertOutputLiveRegionContracts();
    await waitForTabState("upload");
    const requestPanelFetchPath = await fetchViaRequestPanelAndAssert();

    await waitForUploadMethodState("POST");
    await page.locator('[data-upload-method="POST"]').focus();
    await page.keyboard.press("End");
    await waitForUploadMethodState("PATCH", { focused: true });
    await page.keyboard.press("Home");
    await waitForUploadMethodState("POST", { focused: true });

    const uploadName = uploadFilePath.split(/[\\/]/).pop();
    await uploadViaDom(uploadName);

    const uploadSummary = (await page.locator("#uploadResponseArea").innerText()).trim();
    if (!uploadSummary.includes(uploadName)) {
      throw new Error(`Upload response did not mention ${uploadName}`);
    }
    await waitForLiveRegionText("uploadResponseAreaLive", /Загрузка завершена|Upload complete/, 10000);

    await browseUploadsAndAssert(uploadName);
    await waitForLiveRegionText("filesResponseAreaLive", "INFO /uploads 200 OK", 10000);
    await assertFileActionAccessibleNames(uploadName);
    await fetchViaServerFilesAndAssert(uploadName);
    await assertSmuggleDialogKeyboardContract(uploadName);
    const smugglePopupUrl = await smuggleViaServerFilesAndAssert(uploadName);
    const infoPath = await infoViaServerFilesAndAssert(uploadName);
    await browseUploadsAndAssert(uploadName);
    await assertDeleteDialogKeyboardContract(uploadName);
    await deleteViaServerFilesAndAssert(uploadName);
    const opsecAutoSwitch = {
      urlBoundaryNoSwitch: await assertOpsecBoundaryNoSwitch({
        fixturePath: opsecUploadUrlBoundaryFilePath,
        initialTransport: "url",
      }),
      urlToHeaders: await assertOpsecAutoSwitch({
        fixturePath: opsecUploadFilePath,
        initialTransport: "url",
        expectedTransport: "headers",
        expectedWarningFromKey: "opsecTransportUrl",
        expectedWarningToKey: "opsecTransportHeaders",
        expectedWarningTokensRu: ["Заголовки", "URL параметры"],
      }),
      headersBoundaryNoSwitch: await assertOpsecBoundaryNoSwitch({
        fixturePath: opsecUploadBoundaryFilePath,
        initialTransport: "headers",
      }),
      headersToBody: await assertOpsecAutoSwitch({
        fixturePath: opsecUploadLargeFilePath,
        initialTransport: "headers",
        expectedTransport: "body",
        expectedWarningFromKey: "opsecTransportHeaders",
        expectedWarningToKey: "opsecTransportBody",
      }),
      urlToBody: await assertOpsecAutoSwitch({
        fixturePath: opsecUploadLargeFilePath,
        initialTransport: "url",
        expectedTransport: "body",
        expectedWarningFromKey: "opsecTransportUrl",
        expectedWarningToKey: "opsecTransportBody",
      }),
    };

    await page.locator("#tab-notepad").click();
    await waitForTabState("notepad", { focused: true });
    await waitForPageCondition("notepad enabled", () => {
      const titleInput = document.getElementById("notepadTitleInput");
      const textarea = document.getElementById("notepadTextarea");
      return Boolean(titleInput && textarea && !titleInput.disabled && !textarea.disabled);
    }, null, 15000);

    await switchLanguage("ru");
    await assertLocaleSnapshot({
      uploadTabText: "Загрузка",
      filesTabText: "Скачивание",
      opsecTabText: "Загрузка (продвинутая)",
      noteListText: "Нет заметок",
      charCountText: "0 симв.",
      themeLabel: "Переключить тему",
    });
    await switchLanguage("en");
    await assertLocaleSnapshot({
      uploadTabText: "Uploads",
      filesTabText: "Download",
      opsecTabText: "Advanced upload",
      noteListText: "No notes",
      charCountText: "0 chars",
      themeLabel: "Toggle theme",
    });
    await switchLanguage("ru");
    await assertLocaleSnapshot({
      uploadTabText: "Загрузка",
      filesTabText: "Скачивание",
      opsecTabText: "Загрузка (продвинутая)",
      noteListText: "Нет заметок",
      charCountText: "0 симв.",
      themeLabel: "Переключить тему",
    });

    const noteTitle = "Browser Smoke Note";
    const noteText = "browser smoke note body";
    await createAutosavedNote(noteTitle, noteText);
    await switchLanguage("en");
    await waitForText(page.locator("#notepadSaveIndicator"), "Saved", 15000);
    await waitForText(page.locator("#notepadCharCount"), `${noteText.length} chars`, 15000);
    await switchLanguage("ru");
    await waitForText(page.locator("#notepadSaveIndicator"), "Сохранено", 15000);
    await waitForText(page.locator("#notepadCharCount"), `${noteText.length} симв.`, 15000);

    await page.getByRole("button", { name: /Новая|New/ }).click();
    await loadNoteByKeyboard(noteTitle);

    const loadedTitle = await page.locator("#notepadTitleInput").inputValue();
    const loadedText = await page.locator("#notepadTextarea").inputValue();
    if (loadedTitle !== noteTitle) {
      throw new Error(`Loaded note title mismatch: ${loadedTitle}`);
    }
    if (loadedText !== noteText) {
      throw new Error(`Loaded note text mismatch: ${loadedText}`);
    }

    await page.locator("#notepadDeleteBtn").click();
    await confirmAppDialog(noteTitle, 10000);
    await waitForPageCondition(
      `notepad note deleted (${noteTitle})`,
      ([targetTitle]) => {
        const titleInput = document.getElementById("notepadTitleInput");
        const textarea = document.getElementById("notepadTextarea");
        const deleteBtn = document.getElementById("notepadDeleteBtn");
        const noteList = document.getElementById("notepadNoteList");
        return Boolean(
          titleInput &&
          textarea &&
          deleteBtn &&
          noteList &&
          titleInput.value === "" &&
          textarea.value === "" &&
          deleteBtn.disabled &&
          !noteList.innerText.includes(targetTitle)
        );
      },
      [noteTitle],
      15000
    );
    await waitForText(page.locator("#notepadNoteList"), /Нет заметок|No notes/, 15000);

    await page.locator('input[name="notepadTransport"][value="ws"]').check();
    await waitForConnectionStatus("connected", "ws", 15000);

    const wsNoteTitle = "Browser Smoke WS Note";
    const wsNoteText = "browser smoke websocket note body";
    await createAutosavedNote(wsNoteTitle, wsNoteText);

    const wsConnClass = await page.locator("#notepadConnStatus").evaluate((node) => node.className);
    const wsConnState = await page.locator("#notepadConnStatus").getAttribute("data-state");
    const wsConnTransport = await page.locator("#notepadConnStatus").getAttribute("data-transport");
    if (!wsConnClass.includes("connected")) {
      throw new Error(`Unexpected connection class after WS switch: ${wsConnClass}`);
    }
    if (wsConnState !== "connected" || wsConnTransport !== "ws") {
      throw new Error(`Unexpected DOM connection contract after WS switch: state=${wsConnState}; transport=${wsConnTransport}`);
    }

    await page.locator('input[name="notepadTransport"][value="http"]').check();
    await page.getByRole("button", { name: /Новая|New/ }).click();
    await clickNoteByTitle(wsNoteTitle);

    const wsLoadedTitle = await page.locator("#notepadTitleInput").inputValue();
    const wsLoadedText = await page.locator("#notepadTextarea").inputValue();
    if (wsLoadedTitle !== wsNoteTitle) {
      throw new Error(`Cross-transport loaded title mismatch: ${wsLoadedTitle}`);
    }
    if (wsLoadedText !== wsNoteText) {
      throw new Error(`Cross-transport loaded text mismatch: ${wsLoadedText}`);
    }

    const selectiveKeepTitle = "Browser Smoke Selective Keep";
    const selectiveDeleteTitle = "Browser Smoke Selective Delete";
    await createAutosavedNote(selectiveKeepTitle, "keep this note");
    await createAutosavedNote(selectiveDeleteTitle, "delete this note");
    await deleteSelectedNoteViaUiAndAssert(selectiveDeleteTitle, selectiveKeepTitle);

    const notesClearPreservedUpload = await clearNotesViaUiAndAssert(requestPanelFetchPath);
    await deleteSelectedUploadViaUiAndAssert(requestPanelFetchPath);

    const mobileLayout = await assertMobileLayoutSnapshot();

    return {
      ping: "pong",
      uploadedFile: uploadName,
      requestPanelFetchPath,
      infoPath,
      smugglePopupUrl,
      opsecAutoSwitch,
      loadedTitle,
      loadedText,
      wsLoadedTitle,
      wsLoadedText,
      wsConnState,
      wsConnTransport,
      wsConnClass,
      notesClearPreservedUpload,
      selectedUploadDeleted: requestPanelFetchPath,
      selectedNoteDeleted: selectiveDeleteTitle,
      mobileLayout,
    };
  }

  async function runUnavailablePath() {
    async function waitForUnavailableMessage(expectedText, timeout = 15000) {
      await waitForPageCondition(
        `waitForUnavailableMessage(${expectedText})`,
        ([targetText]) => {
          const indicator = document.getElementById("notepadSaveIndicator");
          return Boolean(
            indicator &&
            indicator.textContent &&
            indicator.textContent.includes(targetText)
          );
        },
        [expectedText],
        timeout
      );
    }

    async function getUnavailableSnapshot() {
      return {
        saveIndicator: (await page.locator("#notepadSaveIndicator").textContent() || "").trim(),
        connTitle: await page.locator("#notepadConnStatus").getAttribute("title") || "",
        connClass: await page.locator("#notepadConnStatus").evaluate((node) => node.className),
        connState: await page.locator("#notepadConnStatus").getAttribute("data-state") || "",
        connTransport: await page.locator("#notepadConnStatus").getAttribute("data-transport") || "",
        noteListText: (await page.locator("#notepadNoteList").textContent() || "").trim(),
        titleDisabled: await page.locator("#notepadTitleInput").isDisabled(),
        textareaDisabled: await page.locator("#notepadTextarea").isDisabled(),
        transportsDisabled: await page.locator('input[name="notepadTransport"][value="http"]').isDisabled() &&
          await page.locator('input[name="notepadTransport"][value="ws"]').isDisabled(),
      };
    }

    function assertUnavailableSnapshot(snapshot, expectedUnavailable, localeLabel) {
      if (snapshot.saveIndicator !== expectedUnavailable) {
        throw new Error(`[${localeLabel}] Unexpected unavailable status text: ${snapshot.saveIndicator}`);
      }
      if (!snapshot.connClass.includes("disconnected")) {
        throw new Error(`[${localeLabel}] Unexpected unavailable connection class: ${snapshot.connClass}`);
      }
      if (snapshot.connState !== "disconnected") {
        throw new Error(`[${localeLabel}] Unexpected unavailable connection state: ${snapshot.connState}`);
      }
      if (snapshot.connTransport !== "http") {
        throw new Error(`[${localeLabel}] Unexpected unavailable connection transport: ${snapshot.connTransport}`);
      }
      if (snapshot.connTitle !== expectedUnavailable) {
        throw new Error(`[${localeLabel}] Unexpected unavailable connection tooltip: ${snapshot.connTitle}`);
      }
      if (snapshot.noteListText !== expectedUnavailable) {
        throw new Error(`[${localeLabel}] Unexpected unavailable note list text: ${snapshot.noteListText}`);
      }
      if (!snapshot.titleDisabled || !snapshot.textareaDisabled || !snapshot.transportsDisabled) {
        throw new Error(`[${localeLabel}] Notepad controls were not disabled in unavailable mode`);
      }
    }

    const expectedUnavailableRu =
      "Блокнот недоступен: нужен exphttp[crypto] на сервере.";
    const expectedUnavailableEn =
      "Notepad unavailable: exphttp[crypto] required on server.";

    await switchLanguage("ru");
    await page.locator("#tab-notepad").click();
    await waitForUnavailableMessage(expectedUnavailableRu);
    const ruSnapshot = await getUnavailableSnapshot();
    assertUnavailableSnapshot(ruSnapshot, expectedUnavailableRu, "ru");

    await switchLanguage("en");
    await waitForUnavailableMessage(expectedUnavailableEn);
    const enSnapshot = await getUnavailableSnapshot();
    assertUnavailableSnapshot(enSnapshot, expectedUnavailableEn, "en");

    return {
      ru: ruSnapshot,
      en: enSnapshot,
    };
  }

  await waitForSpaReady();
  await installClipboardMock();
  await page.waitForTimeout(100);
  const happyPath = await runHappyPath();

  if (!unavailableUrl) {
    return { happyPath };
  }

  await page.goto(unavailableUrl, { waitUntil: "domcontentloaded" });
  await waitForSpaReady();
  await page.waitForTimeout(100);
  const unavailablePath = await runUnavailablePath();

  return {
    happyPath,
    unavailablePath,
  };
}
