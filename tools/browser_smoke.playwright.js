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

  async function waitForCapabilityChipPressed(tabName, timeout = 10000) {
    await waitForPageCondition(
      `waitForCapabilityChipPressed(${tabName})`,
      ([targetTabName]) => {
        const chip = document.querySelector(`.capability-chip[data-tab-target="${targetTabName}"]`);
        return Boolean(
          chip &&
          chip.classList.contains("active") &&
          chip.getAttribute("aria-pressed") === "true"
        );
      },
      [tabName],
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

  async function assertCapabilityChipKeyboardActivation(tabName) {
    const chip = page.locator(`.capability-chip[data-tab-target="${tabName}"]`);
    await chip.focus();
    await page.keyboard.press("Enter");
    await waitForCapabilityChipPressed(tabName);
    await waitForTabState(tabName, { focused: true });
  }

  async function browseUploadsAndAssert(name, options = {}) {
    if (options.useCapabilityChip) {
      await page.locator('.capability-chip[data-tab-target="files"]').click();
      await waitForCapabilityChipPressed("files");
      await waitForTabState("files");
      await waitForPageCondition(
        "capability chip pointer activation keeps chip focus",
        () => {
          const chip = document.querySelector('.capability-chip[data-tab-target="files"]');
          return document.activeElement === chip;
        },
        null,
        10000
      );
    } else {
      await page.locator("#tab-files").click();
      await waitForTabState("files", { focused: true });
      await waitForCapabilityChipPressed("files");
    }
    await page.locator("#browsePathInput").fill("/uploads");
    await page.getByRole("button", { name: /Обзор \(INFO\)|Browse \(INFO\)/ }).click();
    await waitForText(page.locator("#serverFiles"), name);
  }

  async function fetchViaRequestPanelAndAssert(name) {
    const requestPath = `/uploads/${name}`;
    await page.locator("#pathInput").fill(requestPath);
    await page.getByRole("button", { name: "FETCH" }).click();
    await waitForText(page.locator("#responseArea"), requestPath);

    const downloadButton = page.locator("#responseArea [data-download-path]");
    await downloadButton.waitFor({ state: "attached", timeout: 10000 });

    const downloadPromise = page.waitForEvent("download");
    await downloadButton.click();
    await waitForPageCondition(
      `request-panel download progress mounted (${name})`,
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
      throw new Error(`Request-panel FETCH download filename mismatch: ${suggestedFilename}`);
    }

    return requestPath;
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
    await waitForCapabilityChipPressed("opsec");

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
        return Boolean(
          uploadBtn &&
          uploadBtn.disabled &&
          warning &&
          warning.hidden === true &&
          selectionState &&
          /No file selected yet|Файл пока не выбран/.test(selectionState.innerText)
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

  async function loadNoteByKeyboard(title) {
    await page.locator("#notepadRefreshBtn").focus();
    await page.keyboard.press("Tab");
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
        const capabilityStrip = document.querySelector(".capability-strip");
        const capabilityChip = document.querySelector(".capability-chip");
        const requestPanel = document.querySelector(".request-panel");
        const statusChip = document.querySelector(".status-chip");
        const liveStatusFull = document.querySelector(".status-chip--live .status-chip__label--full");
        const liveStatusCompact = document.querySelector(".status-chip--live .status-chip__label--compact");
        const heroResponse = document.querySelector(".response-area--hero");

        if (
          !requestSwitch ||
          !capabilityStrip ||
          !capabilityChip ||
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
        const capabilityStripStyles = window.getComputedStyle(capabilityStrip);
        const capabilityChipStyles = window.getComputedStyle(capabilityChip);
        const requestPanelStyles = window.getComputedStyle(requestPanel);
        const statusChipStyles = window.getComputedStyle(statusChip);
        const liveStatusFullStyles = window.getComputedStyle(liveStatusFull);
        const liveStatusCompactStyles = window.getComputedStyle(liveStatusCompact);
        const heroResponseStyles = window.getComputedStyle(heroResponse);

        return (
          doc.scrollWidth <= window.innerWidth + 1 &&
          countColumns(requestSwitchStyles.gridTemplateColumns) === 2 &&
          countColumns(capabilityStripStyles.gridTemplateColumns) === 2 &&
          parseFloat(capabilityChipStyles.paddingTop) <= 12.5 &&
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
      const capabilityStrip = document.querySelector(".capability-strip");
      const capabilityChip = document.querySelector(".capability-chip");
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
      const capabilityStripStyles = window.getComputedStyle(capabilityStrip);
      const capabilityChipStyles = window.getComputedStyle(capabilityChip);
      const requestPanelStyles = window.getComputedStyle(requestPanel);
      const statusChipStyles = window.getComputedStyle(statusChip);
      const liveStatusFullStyles = window.getComputedStyle(liveStatusFull);
      const liveStatusCompactStyles = window.getComputedStyle(liveStatusCompact);
      const heroResponseStyles = window.getComputedStyle(heroResponse);

      return {
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        scrollWidth: doc.scrollWidth,
        requestMethodColumns: countColumns(requestSwitchStyles.gridTemplateColumns),
        capabilityColumns: countColumns(capabilityStripStyles.gridTemplateColumns),
        capabilityChipPaddingTop: parseFloat(capabilityChipStyles.paddingTop),
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
    await page.locator("#pathInput").fill("/");
    await page.getByRole("button", { name: "PING" }).click();
    await waitForText(page.locator("#responseArea"), "pong");
    await waitForLiveRegionText("responseAreaLive", "PING / 200", 10000);

    await waitForUploadMethodState("POST");
    await page.locator('[data-upload-method="POST"]').focus();
    await page.keyboard.press("End");
    await waitForUploadMethodState("PATCH", { focused: true });
    await page.keyboard.press("Home");
    await waitForUploadMethodState("POST", { focused: true });
    await assertCapabilityChipKeyboardActivation("upload");

    const uploadName = uploadFilePath.split(/[\\/]/).pop();
    await uploadViaDom(uploadName);

    const uploadSummary = (await page.locator("#uploadResponseArea").innerText()).trim();
    if (!uploadSummary.includes(uploadName)) {
      throw new Error(`Upload response did not mention ${uploadName}`);
    }
    await waitForLiveRegionText("uploadResponseAreaLive", /Загрузка завершена|Upload complete/, 10000);

    const requestPanelFetchPath = await fetchViaRequestPanelAndAssert(uploadName);
    await browseUploadsAndAssert(uploadName, { useCapabilityChip: true });
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
    await waitForCapabilityChipPressed("notepad");
    await waitForTabState("notepad", { focused: true });
    await waitForPageCondition("notepad enabled", () => {
      const titleInput = document.getElementById("notepadTitleInput");
      const textarea = document.getElementById("notepadTextarea");
      return Boolean(titleInput && textarea && !titleInput.disabled && !textarea.disabled);
    }, null, 15000);

    await switchLanguage("ru");
    await assertLocaleSnapshot({
      uploadTabText: "Загрузка файлов",
      filesTabText: "Файлы на сервере",
      opsecTabText: "Режим OPSEC",
      noteListText: "Заметок пока нет",
      charCountText: "0 симв.",
      themeLabel: "Переключить тему",
    });
    await switchLanguage("en");
    await assertLocaleSnapshot({
      uploadTabText: "Uploads",
      filesTabText: "Files",
      opsecTabText: "OPSEC",
      noteListText: "No notes yet",
      charCountText: "0 chars",
      themeLabel: "Toggle theme",
    });
    await switchLanguage("ru");
    await assertLocaleSnapshot({
      uploadTabText: "Загрузка файлов",
      filesTabText: "Файлы на сервере",
      opsecTabText: "Режим OPSEC",
      noteListText: "Заметок пока нет",
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
    await waitForText(page.locator("#notepadNoteList"), /Заметок пока нет|No notes yet/, 15000);

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
      "Защищённый блокнот недоступен: установите exphttp[crypto] на сервере.";
    const expectedUnavailableEn =
      "Secure Notepad unavailable: install exphttp[crypto] on the server.";

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
