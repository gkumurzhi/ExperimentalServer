// ===== Secure Notepad v2 (ECDH + WebSocket) =====
let notepadCurrentId = null;
let notepadAutoSaveTimer = null;
let notepadSessionId = null;
let notepadDerivedKey = null;   // CryptoKey for AES-GCM
let notepadHasEcdh = false;
let notepadInitDone = false;
let notepadAvailable = false;
let notepadWs = null;

// WS auto-reconnect state
let wsReconnectAttempt = 0;
let wsReconnectTimer = null;
let wsIntentionalClose = false;

// Unsaved changes flag
let notepadIsDirty = false;
let notepadStatusState = 'connecting';
let notepadListCache = [];
let notepadListMode = 'notes';
let notepadEditorInstanceId = 0;
let notepadDirtyVersion = 0;
let notepadActiveSavePromise = null;
let notepadPendingWsSaveSnapshots = [];
let notepadLoadRequestSeq = 0;
let notepadActiveLoadRequestId = null;

const NOTEPAD_HTTP_DELAY = 500;
const NOTEPAD_WS_DELAY = 300;

const notepadTitleInput = document.getElementById('notepadTitleInput');
const notepadTextarea = document.getElementById('notepadTextarea');
const notepadSaveIndicator = document.getElementById('notepadSaveIndicator');
const notepadCharCount = document.getElementById('notepadCharCount');
const notepadNewBtnEl = document.getElementById('notepadNewBtn');
const notepadDeleteBtnEl = document.getElementById('notepadDeleteBtn');
const notepadDeleteSelectedBtnEl = document.getElementById('notepadDeleteSelectedBtn');
const notepadClearBtnEl = document.getElementById('notepadClearBtn');
const notepadRefreshBtnEl = document.getElementById('notepadRefreshBtn');
const notepadConnStatus = document.getElementById('notepadConnStatus');
const notepadConnStatusText = document.getElementById('notepadConnStatusText');
const notepadNoteListEl = document.getElementById('notepadNoteList');
const notepadTransportInputs = Array.from(document.querySelectorAll('input[name="notepadTransport"]'));
const notepadSelectedIds = new Set();
let notepadLastExchangeRequest = null;

function notepadTraceRequest(request, response = null, phase = 'sending') {
    notepadLastExchangeRequest = request || notepadLastExchangeRequest;
    setExchangeInspector('notepad', {
        phase,
        request: notepadLastExchangeRequest || {
            phase: 'empty',
            emptyText: t('exchangeRequestEmpty'),
        },
        response: response || {
            phase,
            startLine: t('statusPending'),
            body: createExchangeTextBody(t('statusPending')),
        },
    });
}

function notepadBuildHttpExchangeRequest(path, body = null, headers = {}) {
    return {
        transport: 'http',
        method: 'NOTE',
        path,
        headers,
        body: body ? createExchangeTextBody(body, { contentType: headers['Content-Type'] || 'application/json' }) : null,
    };
}

function notepadTraceHttpStart(path, body = null, headers = {}) {
    const request = notepadBuildHttpExchangeRequest(path, body, headers);
    notepadTraceRequest(request, {
        phase: 'sending',
        startLine: `NOTE ${path}`,
        body: createExchangeTextBody(t('statusPending')),
    });
    return request;
}

function notepadTraceHttpComplete(request, path, response, text, phase = 'complete') {
    setExchangeInspector('notepad', {
        phase,
        request,
        response: {
            transport: 'http',
            method: 'NOTE',
            path,
            phase,
            startLine: `NOTE ${path}\n${response.status} ${response.statusText || ''}`.trim(),
            status: response.status,
            statusText: response.statusText || '',
            headers: response.headers || {},
            body: createExchangeTextBody(text, { contentType: 'application/json' }),
        },
    });
}

function notepadTraceHttpError(request, path, error) {
    setExchangeInspector('notepad', {
        phase: 'error',
        request,
        response: {
            transport: 'http',
            method: 'NOTE',
            path,
            phase: 'error',
            startLine: `NOTE ${path}\n${t('error')}`,
            body: createExchangeTextBody(error.message || String(error)),
        },
    });
}

if (notepadNewBtnEl) {
    notepadNewBtnEl.addEventListener('click', () => {
        void notepadNewNote();
    });
}

if (notepadDeleteBtnEl) {
    notepadDeleteBtnEl.addEventListener('click', notepadDeleteNote);
}

if (notepadDeleteSelectedBtnEl) {
    notepadDeleteSelectedBtnEl.addEventListener('click', notepadDeleteSelectedNotes);
}

if (notepadClearBtnEl) {
    notepadClearBtnEl.addEventListener('click', notepadClearNotes);
}

if (notepadRefreshBtnEl) {
    notepadRefreshBtnEl.addEventListener('click', notepadRefreshList);
}

if (notepadNoteListEl) {
    notepadNoteListEl.addEventListener('click', (e) => {
        const noteItem = e.target.closest('.note-item[data-note-id]');
        if (!noteItem) return;

        const encodedNoteId = noteItem.dataset.noteId;
        if (encodedNoteId) {
            void notepadLoadNote(decodeURIComponent(encodedNoteId), noteItem);
        }
    });

    notepadNoteListEl.addEventListener('change', (e) => {
        const selectBox = e.target.closest('[data-note-select][data-note-id]');
        if (!selectBox) return;

        const noteId = decodeURIComponent(selectBox.dataset.noteId || '');
        if (!noteId) return;

        if (selectBox.checked) {
            notepadSelectedIds.add(noteId);
        } else {
            notepadSelectedIds.delete(noteId);
        }

        const row = selectBox.closest('.note-row');
        if (row) {
            row.classList.toggle('is-selected', selectBox.checked);
        }
        notepadUpdateSelectedDeleteButton();
    });
}

function notepadSetEditingEnabled(enabled) {
    notepadTitleInput.disabled = !enabled;
    notepadTextarea.disabled = !enabled;
    notepadDeleteBtnEl.disabled = !enabled || !notepadCurrentId;
    notepadDeleteSelectedBtnEl.disabled = !enabled || notepadSelectedIds.size === 0;
    notepadClearBtnEl.disabled = !enabled;
    notepadTransportInputs.forEach(input => {
        input.disabled = !enabled;
    });
}

function notepadUpdateSelectedDeleteButton() {
    if (notepadDeleteSelectedBtnEl) {
        notepadDeleteSelectedBtnEl.disabled = !notepadAvailable || notepadSelectedIds.size === 0;
        notepadDeleteSelectedBtnEl.dataset.count = String(notepadSelectedIds.size);
    }
}

function notepadRenderUnavailable(message) {
    const listEl = document.getElementById('notepadNoteList');
    notepadListMode = 'unavailable';
    notepadListCache = [];
    listEl.innerHTML = '<div class="notepad-no-notes">' + esc(message) + '</div>';
}

function notepadFormatCharCount(count) {
    return count + ' ' + t('charCountSuffix');
}

function notepadFormatListDate(updatedAt) {
    if (!updatedAt) return '';
    const date = new Date(updatedAt);
    if (Number.isNaN(date.getTime())) return '';

    const now = new Date();
    const sameDay =
        date.getFullYear() === now.getFullYear() &&
        date.getMonth() === now.getMonth() &&
        date.getDate() === now.getDate();

    const locale = (document.documentElement.lang || 'ru').startsWith('ru') ? 'ru-RU' : 'en-US';
    const formatOptions = sameDay
        ? { hour: '2-digit', minute: '2-digit' }
        : { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' };

    return new Intl.DateTimeFormat(locale, formatOptions).format(date);
}

function notepadMarkDirty() {
    notepadDirtyVersion++;
    notepadIsDirty = true;
    document.body.classList.add('notepad-dirty');
}

function notepadMarkClean() {
    notepadIsDirty = false;
    document.body.classList.remove('notepad-dirty');
}

function notepadReplaceEditorState() {
    notepadEditorInstanceId++;
    notepadActiveLoadRequestId = null;
    notepadMarkClean();
    clearTimeout(notepadAutoSaveTimer);
    notepadAutoSaveTimer = null;
}

function notepadIsActiveLoad(loadRequestId) {
    return loadRequestId === null || loadRequestId === notepadActiveLoadRequestId;
}

function notepadGetStatusText(state) {
    const stateKeyMap = {
        'connecting': 'notepadConnecting',
        'connected': 'notepadConnected',
        'disconnected': 'notepadDisconnected',
        'ready': 'notepadReady',
        'unsaved': 'notepadUnsaved',
        'saving': 'notepadSaving',
        'saved': 'notepadSaved',
        'loading': 'notepadLoading',
        'loaded': 'notepadLoaded',
        'cleared': 'notepadCleared',
        'selectedDeleted': 'notepadSelectedDeleted',
        'error': 'notepadSaveError',
        'loadError': 'notepadLoadError',
        'decryptError': 'notepadDecryptError',
        'sessionFailed': 'notepadSessionFailed',
        'unavailableServer': 'notepadUnavailableServer',
        'unavailableBrowser': 'notepadUnavailableBrowser',
        'reconnecting': 'notepadReconnecting',
    };
    return t(stateKeyMap[state] || state);
}

function notepadMarkUnavailable(state) {
    const message = notepadGetStatusText(state);
    notepadAvailable = false;
    notepadHasEcdh = false;
    notepadInitDone = true;
    notepadSessionId = null;
    notepadDerivedKey = null;
    notepadCurrentId = null;
    notepadSelectedIds.clear();
    notepadTitleInput.value = '';
    notepadTextarea.value = '';
    notepadCharCount.textContent = notepadFormatCharCount(0);
    notepadReplaceEditorState();
    notepadDisconnectWs(true);
    notepadSetEditingEnabled(false);
    notepadUpdateSelectedDeleteButton();
    notepadSetStatus(state);
    notepadSetConnStatus('disconnected', message);
    notepadRenderUnavailable(message);
}

function notepadGetTransport() {
    const el = document.querySelector('input[name="notepadTransport"]:checked');
    return el ? el.value : 'http';
}

function notepadGetDelay() {
    return notepadGetTransport() === 'ws' ? NOTEPAD_WS_DELAY : NOTEPAD_HTTP_DELAY;
}

// Transport toggle handlers
document.querySelectorAll('input[name="notepadTransport"]').forEach(el => {
    el.addEventListener('change', () => {
        if (!notepadAvailable) return;
        if (el.value === 'ws' && el.checked) {
            notepadConnectWs();
        } else if (el.value === 'http' && el.checked) {
            notepadDisconnectWs(false);
        }
    });
});

// Auto-save on textarea input
notepadTextarea.addEventListener('input', () => {
    notepadCharCount.textContent = notepadFormatCharCount(notepadTextarea.value.length);
    notepadMarkDirty();
    notepadScheduleAutoSave();
});

// Auto-save on title input
notepadTitleInput.addEventListener('input', () => {
    notepadMarkDirty();
    notepadScheduleAutoSave();
});

function notepadScheduleAutoSave() {
    if (!notepadInitDone) return;
    notepadSetStatus('unsaved');
    clearTimeout(notepadAutoSaveTimer);
    notepadAutoSaveTimer = setTimeout(notepadSave, notepadGetDelay());
}

async function notepadConfirmDirtyTransition(options = {}) {
    if (!notepadIsDirty) return true;

    clearTimeout(notepadAutoSaveTimer);
    notepadAutoSaveTimer = null;

    if (notepadActiveSavePromise) {
        const activeSaved = await notepadActiveSavePromise;
        if (activeSaved && !notepadIsDirty) {
            return true;
        }
    }

    const saved = await notepadSave({ forceHttp: true, refreshList: false });
    if (saved && !notepadIsDirty) {
        return true;
    }

    const confirmed = await showConfirmDialog({
        title: t('notepadDiscardTitle'),
        message: t('notepadDiscardConfirm'),
        details: options.details || '',
        confirmLabel: t('notepadDiscardBtn'),
        triggerEl: options.triggerEl || null,
        initialFocus: 'cancel',
    });

    if (confirmed) {
        notepadReplaceEditorState();
        clearTimeout(notepadAutoSaveTimer);
        notepadAutoSaveTimer = null;
        return true;
    }

    notepadSetStatus('unsaved');
    return false;
}

function notepadSetStatus(state) {
    notepadStatusState = state;
    const stateClassMap = {
        'connecting': '',
        'connected': 'saved',
        'disconnected': 'error',
        'ready': '',
        'unsaved': 'unsaved',
        'saving': 'saving',
        'saved': 'saved',
        'error': 'error',
        'loading': 'saving',
        'loaded': 'saved',
        'cleared': 'saved',
        'selectedDeleted': 'saved',
        'loadError': 'error',
        'decryptError': 'error',
        'sessionFailed': 'error',
        'unavailableServer': 'error',
        'unavailableBrowser': 'error',
    };
    const stateClass = stateClassMap[state] || '';
    notepadSaveIndicator.className = 'save-indicator ' + stateClass;
    notepadSaveIndicator.textContent = notepadGetStatusText(state);
}

function notepadSetConnStatus(cls, title) {
    notepadConnStatus.className = 'notepad-connection-status ' + cls;
    notepadConnStatus.dataset.state = cls;
    notepadConnStatus.dataset.transport = notepadGetTransport();
    notepadConnStatus.title = title;
    notepadConnStatus.setAttribute('aria-label', title);
    if (notepadConnStatusText) {
        notepadConnStatusText.textContent = title;
    }
}

function notepadGetConnStatusText(connState) {
    if (notepadStatusState === 'unavailableServer' || notepadStatusState === 'unavailableBrowser') {
        return notepadGetStatusText(notepadStatusState);
    }
    if (notepadStatusState === 'reconnecting') {
        return notepadGetStatusText('reconnecting');
    }

    const connKeyMap = {
        'connecting': 'notepadConnecting',
        'connected': 'notepadConnected',
        'disconnected': 'notepadDisconnected',
    };
    return t(connKeyMap[connState] || 'notepadDisconnected');
}

function notepadRefreshLocale() {
    notepadCharCount.textContent = notepadFormatCharCount(notepadTextarea.value.length);

    if (notepadConnStatus?.dataset?.state) {
        notepadSetConnStatus(
            notepadConnStatus.dataset.state,
            notepadGetConnStatusText(notepadConnStatus.dataset.state)
        );
    }

    if (notepadInitDone) {
        notepadSetStatus(notepadStatusState);
    }

    if (!notepadInitDone) {
        return;
    }

    if (!notepadAvailable) {
        notepadRenderUnavailable(notepadGetStatusText(notepadStatusState));
        return;
    }

    notepadRenderList(notepadListCache);
}

// ── Base64 helpers ──────────────────────────────────────

function uint8ToBase64(bytes) {
    const chunks = [];
    const chunkSize = 8192;
    for (let i = 0; i < bytes.length; i += chunkSize) {
        chunks.push(String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize)));
    }
    return btoa(chunks.join(''));
}

function base64ToUint8(b64) {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
}

// ── ECDH Session Init ───────────────────────────────────

async function notepadInit() {
    if (notepadInitDone) {
        if (notepadAvailable) {
            notepadRefreshList();
        }
        return;
    }
    notepadSetStatus('connecting');
    notepadSetConnStatus('connecting', t('notepadConnecting'));

    try {
        await notepadInitSession();
        notepadAvailable = true;
        notepadInitDone = true;
        notepadSetEditingEnabled(true);
        notepadSetStatus('connected');
        notepadSetConnStatus('connected', t('notepadConnected'));
        notepadRefreshList();
    } catch (e) {
        if (e && e.message === 'server-crypto-unavailable') {
            console.warn('[Notepad] Secure Notepad unavailable on server:', e);
            notepadMarkUnavailable('unavailableServer');
        } else if (e && e.message === 'browser-crypto-unavailable') {
            console.warn('[Notepad] Secure Notepad unavailable in browser:', e);
            notepadMarkUnavailable('unavailableBrowser');
        } else {
            console.error('[Notepad] Session init failed:', e);
            notepadMarkUnavailable('sessionFailed');
        }
    }
}

async function notepadInitSession() {
    if (!window.crypto || !window.crypto.subtle) {
        throw new Error('browser-crypto-unavailable');
    }

    // 1. Get server public key
    const keyTrace = notepadTraceHttpStart('/notes/key');
    const keyResp = await sendCustomRequest('NOTE', SERVER_URL + '/notes/key');
    const keyText = await keyResp.text();
    notepadTraceHttpComplete(keyTrace, '/notes/key', keyResp, keyText, keyResp.ok ? 'complete' : 'error');
    if (!keyResp.ok) {
        throw new Error(keyResp.status === 501 ? 'server-crypto-unavailable' : 'session-init-failed');
    }
    const keyData = JSON.parse(keyText);

    if (!keyData.hasEcdh || typeof keyData.publicKey !== 'string' || !keyData.publicKey) {
        throw new Error('server-crypto-unavailable');
    }

    // 2. Generate client ECDH key pair
    const clientKeyPair = await crypto.subtle.generateKey(
        { name: 'ECDH', namedCurve: 'P-256' },
        true,
        ['deriveBits']
    );

    // 3. Exchange keys
    const clientPubRaw = await crypto.subtle.exportKey('raw', clientKeyPair.publicKey);
    const clientPubB64 = uint8ToBase64(new Uint8Array(clientPubRaw));

    const exchangeBody = JSON.stringify({ clientPublicKey: clientPubB64 });
    const exchangeTrace = notepadTraceHttpStart('/notes/exchange', exchangeBody, { 'Content-Type': 'application/json' });
    const exchangeResp = await sendCustomRequest('NOTE', SERVER_URL + '/notes/exchange',
        exchangeBody,
        { 'Content-Type': 'application/json' }
    );
    const exchangeText = await exchangeResp.text();
    notepadTraceHttpComplete(exchangeTrace, '/notes/exchange', exchangeResp, exchangeText, exchangeResp.ok ? 'complete' : 'error');
    if (!exchangeResp.ok) {
        throw new Error(
            exchangeResp.status === 501 ? 'server-crypto-unavailable' : 'session-init-failed'
        );
    }
    const exchangeData = JSON.parse(exchangeText);
    if (typeof exchangeData.sessionId !== 'string' || typeof exchangeData.serverPublicKey !== 'string') {
        throw new Error('session-init-failed');
    }
    notepadSessionId = exchangeData.sessionId;

    // 4. Import server public key
    const serverPubRaw = base64ToUint8(exchangeData.serverPublicKey);
    const serverPubKey = await crypto.subtle.importKey(
        'raw', serverPubRaw,
        { name: 'ECDH', namedCurve: 'P-256' },
        false,
        []
    );

    // 5. Derive shared bits
    const sharedBits = await crypto.subtle.deriveBits(
        { name: 'ECDH', public: serverPubKey },
        clientKeyPair.privateKey,
        256
    );

    // 6. HKDF to get AES-256 key
    const sharedKeyMaterial = await crypto.subtle.importKey(
        'raw', sharedBits, 'HKDF', false, ['deriveKey']
    );

    notepadDerivedKey = await crypto.subtle.deriveKey(
        {
            name: 'HKDF',
            hash: 'SHA-256',
            salt: new Uint8Array(32),  // 32 zero bytes
            info: new TextEncoder().encode('notepad-e2e-key'),
        },
        sharedKeyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
    );

    notepadHasEcdh = true;
}

// ── ECDH encrypt/decrypt ────────────────────────────────

async function notepadEncrypt(text) {
    const enc = new TextEncoder();
    const plaintext = enc.encode(text);
    const nonce = crypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv: nonce },
        notepadDerivedKey,
        plaintext
    );
    // Wire format: nonce(12) + ciphertext + tag(16)
    const result = new Uint8Array(12 + ciphertext.byteLength);
    result.set(nonce, 0);
    result.set(new Uint8Array(ciphertext), 12);
    return result;
}

async function notepadDecrypt(encryptedBytes) {
    if (encryptedBytes.length < 12 + 16) throw new Error('Data too short');
    const nonce = encryptedBytes.slice(0, 12);
    const ciphertext = encryptedBytes.slice(12);
    const plaintext = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: nonce },
        notepadDerivedKey,
        ciphertext
    );
    return new TextDecoder().decode(plaintext);
}

// ── WebSocket client ────────────────────────────────────

function scheduleReconnect() {
    if (wsIntentionalClose) return;
    const delay = Math.min(1000 * Math.pow(2, wsReconnectAttempt), 30000);
    wsReconnectAttempt++;
    notepadSetConnStatus('disconnected', t('notepadReconnecting'));
    wsReconnectTimer = setTimeout(() => {
        if (notepadGetTransport() === 'ws' && !wsIntentionalClose) {
            notepadConnectWs();
        }
    }, delay);
}

function notepadConnectWs() {
    if (!notepadAvailable) return;
    notepadDisconnectWs(true);
    wsIntentionalClose = false;
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    notepadWs = new WebSocket(proto + '//' + location.host + '/notes/ws');
    notepadSetConnStatus('connecting', t('notepadConnecting'));

    notepadWs.onopen = () => {
        wsReconnectAttempt = 0;
        notepadSetConnStatus('connected', t('notepadConnected'));
    };

    notepadWs.onmessage = (evt) => {
        try {
            const msg = JSON.parse(evt.data);
            notepadHandleWsMessage(msg, evt.data);
        } catch (e) {
            console.error('[Notepad WS] Parse error:', e);
        }
    };

    notepadWs.onclose = () => {
        notepadWs = null;
        if (!wsIntentionalClose && notepadGetTransport() === 'ws') {
            scheduleReconnect();
        } else if (!wsIntentionalClose) {
            notepadSetConnStatus('disconnected', t('notepadDisconnected'));
        }
    };

    notepadWs.onerror = () => {
        // onclose will fire after this
    };
}

function notepadDisconnectWs(skipStatus) {
    wsIntentionalClose = true;
    if (wsReconnectTimer) { clearTimeout(wsReconnectTimer); wsReconnectTimer = null; }
    if (notepadWs) {
        notepadWs.close();
        notepadWs = null;
    }
    if (!skipStatus) {
        notepadSetConnStatus('connected', t('notepadConnected'));
    }
}

function notepadSendWs(msg) {
    if (notepadWs && notepadWs.readyState === WebSocket.OPEN) {
        const messageText = JSON.stringify(msg);
        notepadTraceRequest({
            transport: 'ws',
            type: msg.type || 'message',
            path: '/notes/ws',
            body: createExchangeTextBody(messageText, { contentType: 'application/json' }),
        }, {
            transport: 'ws',
            phase: 'sending',
            path: '/notes/ws',
            body: createExchangeTextBody(t('statusPending')),
        });
        notepadWs.send(messageText);
    }
}

function notepadCaptureSaveSnapshot() {
    const titleRaw = notepadTitleInput.value.trim();
    return {
        editorInstanceId: notepadEditorInstanceId,
        dirtyVersion: notepadDirtyVersion,
        noteId: notepadCurrentId || '',
        titleRaw,
        title: titleRaw || t('notepadUntitled'),
        text: notepadTextarea.value,
        sessionId: notepadSessionId || '',
    };
}

function notepadApplySaveSuccess(snapshot, result, options = {}) {
    const sameEditor = snapshot && snapshot.editorInstanceId === notepadEditorInstanceId;

    if (sameEditor) {
        if (!snapshot.noteId && !notepadCurrentId && result.id) {
            notepadCurrentId = result.id;
        }
        notepadDeleteBtnEl.disabled = false;

        if (snapshot.dirtyVersion === notepadDirtyVersion) {
            notepadMarkClean();
            notepadSetStatus('saved');
        } else if (notepadIsDirty) {
            notepadSetStatus('unsaved');
        }
    }

    if (options.refreshList !== false) {
        notepadRefreshList();
    }
}

function notepadHandleWsMessage(msg, rawText = '') {
    setExchangeInspector('notepad', {
        phase: msg.type === 'error' ? 'error' : 'complete',
        request: notepadLastExchangeRequest || {
            transport: 'ws',
            type: 'message',
            path: '/notes/ws',
            body: null,
        },
        response: {
            transport: 'ws',
            type: msg.type || 'message',
            path: '/notes/ws',
            phase: msg.type === 'error' ? 'error' : 'complete',
            body: createExchangeJsonBody(msg, { rawText }),
        },
    });

    if (msg.type === 'saved') {
        if (msg.success) {
            const snapshot = notepadPendingWsSaveSnapshots.shift() || null;
            if (snapshot) {
                notepadApplySaveSuccess(snapshot, msg);
            }
        } else {
            notepadSetStatus('error');
        }
    } else if (msg.type === 'loaded') {
        notepadHandleLoadResult(msg);
    } else if (msg.type === 'list') {
        notepadRenderList(msg.notes || []);
    } else if (msg.type === 'deleted') {
        notepadApplyNewNoteState();
    } else if (msg.type === 'cleared') {
        notepadApplyClearResult(msg);
    } else if (msg.type === 'error') {
        console.error('[Notepad WS] Server error:', msg.error);
        notepadSetStatus('error');
    }
}

// ── CRUD operations ─────────────────────────────────────

async function notepadSave(options = {}) {
    const savePromise = notepadRunSave(options);
    notepadActiveSavePromise = savePromise;
    try {
        return await savePromise;
    } finally {
        if (notepadActiveSavePromise === savePromise) {
            notepadActiveSavePromise = null;
        }
    }
}

async function notepadRunSave(options = {}) {
    if (!notepadAvailable || !notepadDerivedKey) {
        notepadSetStatus('sessionFailed');
        return false;
    }
    clearTimeout(notepadAutoSaveTimer);
    notepadAutoSaveTimer = null;

    const snapshot = notepadCaptureSaveSnapshot();

    if (!snapshot.text && !snapshot.titleRaw && !snapshot.noteId) return false;

    notepadSetStatus('saving');

    try {
        const encrypted = await notepadEncrypt(snapshot.text);
        const dataB64 = uint8ToBase64(encrypted);

        if (!options.forceHttp && notepadGetTransport() === 'ws' && notepadWs && notepadWs.readyState === WebSocket.OPEN) {
            // WebSocket save
            notepadPendingWsSaveSnapshots.push(snapshot);
            notepadSendWs({
                type: 'save',
                sessionId: snapshot.sessionId,
                noteId: snapshot.noteId,
                title: snapshot.title,
                data: dataB64,
            });
            return true;
        } else {
            // HTTP save
            const payload = { title: snapshot.title, data: dataB64 };
            if (snapshot.noteId) payload.id = snapshot.noteId;

            const headers = { 'Content-Type': 'application/json' };
            if (snapshot.sessionId) headers['X-Session-Id'] = snapshot.sessionId;

            const body = JSON.stringify(payload);
            const trace = notepadTraceHttpStart('/notes', body, headers);
            const response = await sendCustomRequest('NOTE', SERVER_URL + '/notes', body, headers);
            const respText = await response.text();
            notepadTraceHttpComplete(trace, '/notes', response, respText, response.ok ? 'complete' : 'error');
            const result = JSON.parse(respText);

            if (result.success) {
                notepadApplySaveSuccess(snapshot, result, options);
                return true;
            } else {
                notepadSetStatus('error');
                return false;
            }
        }
    } catch (e) {
        console.error('[Notepad] Save error:', e);
        notepadSetStatus('error');
        return false;
    }
}

async function notepadRefreshList() {
    if (!notepadAvailable) return;
    if (notepadGetTransport() === 'ws' && notepadWs && notepadWs.readyState === WebSocket.OPEN) {
        notepadSendWs({ type: 'list' });
        return;
    }

    try {
        const trace = notepadTraceHttpStart('/notes?list');
        const response = await sendCustomRequest('NOTE', SERVER_URL + '/notes?list');
        const text = await response.text();
        notepadTraceHttpComplete(trace, '/notes?list', response, text, response.ok ? 'complete' : 'error');
        const result = JSON.parse(text);
        notepadRenderList(result.notes || []);
    } catch (e) {
        console.error('[Notepad] List error:', e);
    }
}

function notepadRenderList(notes) {
    const listEl = document.getElementById('notepadNoteList');
    notepadListMode = 'notes';
    notepadListCache = Array.isArray(notes) ? notes : [];
    if (!notes || notes.length === 0) {
        notepadSelectedIds.clear();
        notepadUpdateSelectedDeleteButton();
        listEl.innerHTML = '<div class="notepad-no-notes">' + esc(t('notepadNoNotes')) + '</div>';
        return;
    }

    const visibleIds = new Set(notes.map(note => note.id).filter(Boolean));
    Array.from(notepadSelectedIds).forEach(noteId => {
        if (!visibleIds.has(noteId)) {
            notepadSelectedIds.delete(noteId);
        }
    });
    notepadUpdateSelectedDeleteButton();

    listEl.innerHTML = notes.map(note => {
        const isActive = note.id === notepadCurrentId;
        const isSelected = notepadSelectedIds.has(note.id);
        const date = notepadFormatListDate(note.updated_at);
        const encodedNoteId = encodeURIComponent(note.id);
        const selectLabel = esc(`${t('selectNoteLabel')}: ${note.title || t('notepadUntitled')}`);
        return '<div class="note-row' + (isActive ? ' active' : '') + (isSelected ? ' is-selected' : '') + '">' +
            '<label class="note-select" title="' + selectLabel + '" aria-label="' + selectLabel + '">' +
            '<input type="checkbox" data-note-select data-note-id="' + encodedNoteId + '"' + (isSelected ? ' checked' : '') + '>' +
            '<span aria-hidden="true"></span>' +
            '</label>' +
            '<button type="button" class="note-item' + (isActive ? ' active' : '') + '" data-note-id="' + encodedNoteId + '"' +
            (isActive ? ' aria-current="true"' : '') + '>' +
            '<div class="note-item-title">' + esc(note.title || t('notepadUntitled')) + '</div>' +
            '<div class="note-item-date">' + esc(date) + '</div>' +
            '</button>' +
            '</div>';
    }).join('');
}

async function notepadLoadNote(id, triggerEl = null) {
    if (!notepadAvailable || !notepadDerivedKey) {
        notepadSetStatus('sessionFailed');
        return;
    }
    if (id === notepadCurrentId) {
        return;
    }

    if (notepadIsDirty) {
        const targetNote = notepadListCache.find(note => note.id === id);
        const canReplaceEditor = await notepadConfirmDirtyTransition({
            triggerEl,
            details: targetNote ? (targetNote.title || t('notepadUntitled')) : id,
        });
        if (!canReplaceEditor) return;
    }

    notepadSetStatus('loading');
    const loadRequestId = ++notepadLoadRequestSeq;
    notepadActiveLoadRequestId = loadRequestId;

    try {
        const path = '/notes/' + id;
        const trace = notepadTraceHttpStart(path);
        const response = await sendCustomRequest('NOTE', SERVER_URL + path);
        const text = await response.text();
        notepadTraceHttpComplete(trace, path, response, text, response.ok ? 'complete' : 'error');
        const result = JSON.parse(text);

        if (!notepadIsActiveLoad(loadRequestId)) {
            return;
        }

        if (response.status === 404) {
            notepadSetStatus('loadError');
            return;
        }

        await notepadHandleLoadResult(result, { loadRequestId });
    } catch (e) {
        if (!notepadIsActiveLoad(loadRequestId)) {
            return;
        }
        console.error('[Notepad] Load error:', e);
        notepadSetStatus('loadError');
    }
}

async function notepadHandleLoadResult(result, options = {}) {
    try {
        if (!notepadAvailable || !notepadDerivedKey) {
            notepadSetStatus('sessionFailed');
            return;
        }
        const loadRequestId = options.loadRequestId || null;
        if (!notepadIsActiveLoad(loadRequestId)) {
            return;
        }

        const encryptedBytes = base64ToUint8(result.data);
        const plaintext = await notepadDecrypt(encryptedBytes);
        if (!notepadIsActiveLoad(loadRequestId) || notepadIsDirty) {
            return;
        }

        notepadReplaceEditorState();
        notepadCurrentId = result.id;
        notepadTitleInput.value = result.title || '';
        notepadTextarea.value = plaintext;
        notepadCharCount.textContent = notepadFormatCharCount(plaintext.length);
        notepadDeleteBtnEl.disabled = false;
        notepadSetStatus('loaded');
        notepadRefreshList();
    } catch (e) {
        console.error('[Notepad] Decrypt/load error:', e);
        if (e.name === 'OperationError' || (e.message && e.message.includes('decrypt'))) {
            notepadSetStatus('decryptError');
        } else {
            notepadSetStatus('loadError');
        }
    }
}

function notepadApplyNewNoteState() {
    notepadReplaceEditorState();
    notepadCurrentId = null;
    notepadTitleInput.value = '';
    notepadTextarea.value = '';
    notepadCharCount.textContent = notepadFormatCharCount(0);
    notepadDeleteBtnEl.disabled = true;
    if (!notepadInitDone) {
        notepadSetStatus('connecting');
    } else if (!notepadAvailable) {
        notepadSetStatus('sessionFailed');
    } else {
        notepadSetStatus('ready');
        notepadTitleInput.focus();
    }
    notepadRefreshList();
}

async function notepadNewNote(options = {}) {
    if (!options.skipDirtyGuard && notepadIsDirty) {
        const canReplaceEditor = await notepadConfirmDirtyTransition({
            triggerEl: options.triggerEl || notepadNewBtnEl,
            details: notepadTitleInput.value.trim() || t('notepadUntitled'),
        });
        if (!canReplaceEditor) return false;
    }

    notepadApplyNewNoteState();
    return true;
}

async function notepadDeleteNote() {
    if (!notepadCurrentId) return;
    const noteTitle = notepadTitleInput.value.trim() || t('notepadUntitled');
    const confirmed = await showConfirmDialog({
        title: t('notepadDeleteBtn'),
        message: t('notepadDeleteConfirm'),
        details: noteTitle,
        confirmLabel: t('notepadDeleteBtn'),
        triggerEl: notepadDeleteBtnEl,
        initialFocus: 'cancel',
    });
    if (!confirmed) return;

    try {
        if (notepadGetTransport() === 'ws' && notepadWs && notepadWs.readyState === WebSocket.OPEN) {
            notepadSendWs({ type: 'delete', id: notepadCurrentId });
        } else {
            const path = '/notes/' + notepadCurrentId + '?delete';
            const trace = notepadTraceHttpStart(path);
            const response = await sendCustomRequest('NOTE', SERVER_URL + path);
            const text = await response.text();
            notepadTraceHttpComplete(trace, path, response, text, response.ok ? 'complete' : 'error');
            let result = null;
            try {
                result = JSON.parse(text);
            } catch (error) {
                result = null;
            }

            if (response.ok && result && result.success) {
                notepadApplyNewNoteState();
                return;
            }

            notepadSetStatus('error');
            await showNoticeDialog({
                title: t('notepadDeleteError'),
                message: (result && result.error) || text || `${response.status} ${response.statusText || t('error')}`.trim(),
                details: noteTitle,
                triggerEl: notepadDeleteBtnEl,
            });
            return;
        }
    } catch (e) {
        console.error('[Notepad] Delete error:', e);
        notepadSetStatus('error');
        await showNoticeDialog({
            title: t('notepadDeleteError'),
            message: e.message,
            details: noteTitle,
            triggerEl: notepadDeleteBtnEl,
        });
    }
}

function notepadResetEditorAfterDelete() {
    notepadReplaceEditorState();
    notepadCurrentId = null;
    notepadTitleInput.value = '';
    notepadTextarea.value = '';
    notepadCharCount.textContent = notepadFormatCharCount(0);
    notepadDeleteBtnEl.disabled = true;
}

async function notepadDeleteSelectedNotes() {
    if (!notepadAvailable || notepadSelectedIds.size === 0) return;

    const selectedIds = Array.from(notepadSelectedIds);
    const selectedTitles = selectedIds.map(noteId => {
        const note = notepadListCache.find(item => item.id === noteId);
        return note ? (note.title || t('notepadUntitled')) : noteId;
    });

    const confirmed = await showConfirmDialog({
        title: t('notepadDeleteSelectedBtn'),
        message: t('notepadDeleteSelectedConfirm'),
        details: selectedTitles.join('\n'),
        confirmLabel: t('notepadDeleteSelectedBtn'),
        triggerEl: notepadDeleteSelectedBtnEl,
        initialFocus: 'cancel',
    });
    if (!confirmed) return;

    const deletedCurrent = selectedIds.includes(notepadCurrentId);
    const errors = [];

    for (const noteId of selectedIds) {
        try {
            const path = '/notes/' + noteId + '?delete';
            const trace = notepadTraceHttpStart(path);
            const response = await sendCustomRequest('NOTE', SERVER_URL + path);
            const text = await response.text();
            notepadTraceHttpComplete(trace, path, response, text, response.ok ? 'complete' : 'error');
            let result = null;
            try {
                result = JSON.parse(text);
            } catch (error) {
                result = null;
            }

            if (response.ok && result && result.success) {
                notepadSelectedIds.delete(noteId);
            } else {
                const message = (result && result.error) || text || `${response.status} ${response.statusText || t('error')}`.trim();
                errors.push(`${noteId}: ${message}`);
            }
        } catch (e) {
            errors.push(`${noteId}: ${e.message}`);
        }
    }

    if (deletedCurrent) {
        notepadResetEditorAfterDelete();
    }
    notepadUpdateSelectedDeleteButton();
    await notepadRefreshList();

    if (errors.length) {
        notepadSetStatus('error');
        await showNoticeDialog({
            title: t('notepadDeleteError'),
            message: errors.join('\n'),
            details: t('notepadDeleteSelectedBtn'),
            triggerEl: notepadDeleteSelectedBtnEl,
        });
        return;
    }

    notepadSetStatus('selectedDeleted');
}

function notepadApplyClearResult(result) {
    if (!result || !result.success) {
        notepadSetStatus('error');
        return false;
    }

    notepadSelectedIds.clear();
    notepadUpdateSelectedDeleteButton();
    notepadResetEditorAfterDelete();
    notepadRenderList([]);
    notepadSetStatus('cleared');
    return true;
}

async function notepadClearNotes() {
    if (!notepadAvailable) return;

    const confirmed = await showConfirmDialog({
        title: t('notepadClearBtn'),
        message: t('notepadClearConfirm'),
        details: '/notes',
        confirmLabel: t('notepadClearBtn'),
        triggerEl: notepadClearBtnEl,
        initialFocus: 'cancel',
    });
    if (!confirmed) return;

    try {
        const trace = notepadTraceHttpStart('/notes?clear=1');
        const response = await sendCustomRequest('NOTE', SERVER_URL + '/notes?clear=1');
        const text = await response.text();
        notepadTraceHttpComplete(trace, '/notes?clear=1', response, text, response.ok ? 'complete' : 'error');
        let result = null;
        try {
            result = JSON.parse(text);
        } catch (error) {
            result = null;
        }

        if (response.ok && notepadApplyClearResult(result)) {
            return;
        }

        notepadSetStatus('error');
        await showNoticeDialog({
            title: t('notepadClearError'),
            message: (result && result.error) || text || `${response.status} ${response.statusText || t('error')}`.trim(),
            details: '/notes',
            triggerEl: notepadClearBtnEl,
        });
    } catch (e) {
        console.error('[Notepad] Clear error:', e);
        notepadSetStatus('error');
        await showNoticeDialog({
            title: t('notepadClearError'),
            message: e.message,
            details: '/notes',
            triggerEl: notepadClearBtnEl,
        });
    }
}
