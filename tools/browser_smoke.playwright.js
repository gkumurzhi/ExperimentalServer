async (page) => {
  const unavailableUrl = __EXPHTTP_UNAVAILABLE_URL__;

  async function waitForSpaReady() {
    await page.waitForLoadState('domcontentloaded');
    await page.waitForFunction(() => typeof window.sendCustomRequest === 'function');
  }

  async function runHappyPath() {
    return await page.evaluate(async () => {
      async function waitFor(predicate, errorMessage, timeoutMs = 5000, stepMs = 50) {
        const deadline = Date.now() + timeoutMs;
        while (Date.now() < deadline) {
          if (predicate()) {
            return;
          }
          await new Promise((resolve) => setTimeout(resolve, stepMs));
        }
        throw new Error(errorMessage);
      }

      async function setNotepadTransport(transport) {
        const transportInput = document.querySelector(
          `input[name="notepadTransport"][value="${transport}"]`
        );
        if (!transportInput) {
          throw new Error(`Missing notepad transport input: ${transport}`);
        }
        transportInput.click();
        await waitFor(
          () => notepadGetTransport() === transport,
          `Notepad transport did not switch to ${transport}`
        );
      }

      const pingResponse = await sendCustomRequest('PING', SERVER_URL + '/');
      const pingBody = JSON.parse(await pingResponse.text());
      if (pingResponse.status !== 200 || pingBody.status !== 'pong') {
        throw new Error(`PING failed with ${pingResponse.status}`);
      }

      const uploadName = 'browser-smoke-upload.txt';
      const uploadContents = 'browser smoke upload\n';
      handleFiles([new File([uploadContents], uploadName, { type: 'text/plain' })]);
      await uploadAllFiles();

      const uploadSummary = document.getElementById('uploadResponseArea')?.innerText || '';
      if (!uploadSummary.includes(uploadName)) {
        throw new Error(`Upload response did not mention ${uploadName}`);
      }

      document.getElementById('browsePathInput').value = '/uploads';
      await browseDirectory();
      const browseSummary = document.getElementById('serverFiles')?.innerText || '';
      if (!browseSummary.includes(uploadName)) {
        throw new Error(`Browse results did not include ${uploadName}`);
      }

      switchTab('notepad', document.getElementById('tab-notepad'));
      await notepadInit();
      if (!notepadAvailable || !notepadDerivedKey) {
        throw new Error('Notepad session did not initialize');
      }

      const noteTitle = 'Browser Smoke Note';
      const noteText = 'browser smoke note body';
      notepadNewNote();
      document.getElementById('notepadTitleInput').value = noteTitle;
      document.getElementById('notepadTitleInput').dispatchEvent(new Event('input', { bubbles: true }));
      document.getElementById('notepadTextarea').value = noteText;
      document.getElementById('notepadTextarea').dispatchEvent(new Event('input', { bubbles: true }));
      await notepadSave();

      if (!notepadCurrentId) {
        throw new Error('Notepad save did not produce a note id');
      }
      const noteId = notepadCurrentId;

      notepadNewNote();
      await notepadLoadNote(noteId);

      const loadedTitle = document.getElementById('notepadTitleInput').value;
      const loadedText = document.getElementById('notepadTextarea').value;
      if (loadedTitle !== noteTitle) {
        throw new Error(`Loaded note title mismatch: ${loadedTitle}`);
      }
      if (loadedText !== noteText) {
        throw new Error(`Loaded note text mismatch: ${loadedText}`);
      }

      await setNotepadTransport('ws');
      await waitFor(
        () => notepadWs && notepadWs.readyState === WebSocket.OPEN,
        'Notepad WebSocket did not connect'
      );

      const wsConnClass = document.getElementById('notepadConnStatus')?.className || '';
      if (!wsConnClass.includes('connected')) {
        throw new Error(`Unexpected WebSocket connection class: ${wsConnClass}`);
      }

      const wsNoteTitle = 'Browser Smoke WS Note';
      const wsNoteText = 'browser smoke websocket note body';
      notepadNewNote();
      document.getElementById('notepadTitleInput').value = wsNoteTitle;
      document.getElementById('notepadTitleInput').dispatchEvent(new Event('input', { bubbles: true }));
      document.getElementById('notepadTextarea').value = wsNoteText;
      document.getElementById('notepadTextarea').dispatchEvent(new Event('input', { bubbles: true }));
      await notepadSave();
      await waitFor(() => Boolean(notepadCurrentId), 'WebSocket save did not produce a note id');

      const wsNoteId = notepadCurrentId;
      await waitFor(
        () => document.getElementById('notepadNoteList')?.innerText.includes(wsNoteTitle),
        `WebSocket list did not include ${wsNoteTitle}`
      );

      await setNotepadTransport('http');
      await waitFor(
        () => !notepadWs || notepadWs.readyState === WebSocket.CLOSED,
        'Notepad WebSocket did not disconnect after switching back to HTTP'
      );

      notepadNewNote();
      await notepadLoadNote(wsNoteId);

      const wsLoadedTitle = document.getElementById('notepadTitleInput').value;
      const wsLoadedText = document.getElementById('notepadTextarea').value;
      if (wsLoadedTitle !== wsNoteTitle) {
        throw new Error(`Cross-transport loaded title mismatch: ${wsLoadedTitle}`);
      }
      if (wsLoadedText !== wsNoteText) {
        throw new Error(`Cross-transport loaded text mismatch: ${wsLoadedText}`);
      }

      return {
        ping: pingBody.status,
        uploadedFile: uploadName,
        noteId,
        loadedTitle,
        loadedText,
        wsNoteId,
        wsLoadedTitle,
        wsLoadedText,
        wsConnClass,
      };
    });
  }

  async function runUnavailablePath() {
    return await page.evaluate(async () => {
      switchTab('notepad', document.getElementById('tab-notepad'));
      await notepadInit();

      const unavailableMessage = t('notepadUnavailableServer');
      const saveIndicator = document.getElementById('notepadSaveIndicator')?.textContent?.trim() || '';
      const connTitle = document.getElementById('notepadConnStatus')?.title || '';
      const connClass = document.getElementById('notepadConnStatus')?.className || '';
      const noteListText = document.getElementById('notepadNoteList')?.textContent?.trim() || '';
      const titleDisabled = Boolean(document.getElementById('notepadTitleInput')?.disabled);
      const textareaDisabled = Boolean(document.getElementById('notepadTextarea')?.disabled);
      const transportsDisabled = Array.from(
        document.querySelectorAll('input[name="notepadTransport"]')
      ).every((input) => input.disabled);

      if (!notepadInitDone) {
        throw new Error('Notepad unavailable flow never completed initialization');
      }
      if (notepadAvailable || notepadDerivedKey || notepadSessionId) {
        throw new Error('Notepad unavailable flow left an active session behind');
      }
      if (saveIndicator !== unavailableMessage) {
        throw new Error(`Unexpected unavailable status text: ${saveIndicator}`);
      }
      if (!connClass.includes('disconnected')) {
        throw new Error(`Unexpected unavailable connection class: ${connClass}`);
      }
      if (!connTitle) {
        throw new Error('Unavailable connection status tooltip was empty');
      }
      if (!titleDisabled || !textareaDisabled || !transportsDisabled) {
        throw new Error('Notepad controls were not disabled in unavailable mode');
      }

      return {
        saveIndicator,
        connTitle,
        connClass,
        noteListText,
        titleDisabled,
        textareaDisabled,
        transportsDisabled,
      };
    });
  }

  await waitForSpaReady();
  await page.waitForTimeout(100);
  const happyPath = await runHappyPath();

  if (!unavailableUrl) {
    return { happyPath };
  }

  await page.goto(unavailableUrl, { waitUntil: 'domcontentloaded' });
  await waitForSpaReady();
  await page.waitForTimeout(100);
  const unavailablePath = await runUnavailablePath();

  return {
    happyPath,
    unavailablePath,
  };
}
