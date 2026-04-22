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

const NOTEPAD_HTTP_DELAY = 500;
const NOTEPAD_WS_DELAY = 300;

const notepadTitleInput = document.getElementById('notepadTitleInput');
const notepadTextarea = document.getElementById('notepadTextarea');
const notepadSaveIndicator = document.getElementById('notepadSaveIndicator');
const notepadCharCount = document.getElementById('notepadCharCount');
const notepadNewBtnEl = document.getElementById('notepadNewBtn');
const notepadDeleteBtnEl = document.getElementById('notepadDeleteBtn');
const notepadRefreshBtnEl = document.getElementById('notepadRefreshBtn');
const notepadConnStatus = document.getElementById('notepadConnStatus');
const notepadNoteListEl = document.getElementById('notepadNoteList');
const notepadTransportInputs = Array.from(document.querySelectorAll('input[name="notepadTransport"]'));

if (notepadNewBtnEl) {
    notepadNewBtnEl.addEventListener('click', notepadNewNote);
}

if (notepadDeleteBtnEl) {
    notepadDeleteBtnEl.addEventListener('click', notepadDeleteNote);
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
            notepadLoadNote(decodeURIComponent(encodedNoteId));
        }
    });
}

function notepadSetEditingEnabled(enabled) {
    notepadTitleInput.disabled = !enabled;
    notepadTextarea.disabled = !enabled;
    notepadDeleteBtnEl.disabled = !enabled || !notepadCurrentId;
    notepadTransportInputs.forEach(input => {
        input.disabled = !enabled;
    });
}

function notepadRenderUnavailable(message) {
    const listEl = document.getElementById('notepadNoteList');
    listEl.innerHTML = '<div class="notepad-no-notes">' + esc(message) + '</div>';
}

function notepadFormatCharCount(count) {
    return count + ' ' + t('charCountSuffix');
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
    notepadTitleInput.value = '';
    notepadTextarea.value = '';
    notepadCharCount.textContent = notepadFormatCharCount(0);
    notepadIsDirty = false;
    document.body.classList.remove('notepad-dirty');
    clearTimeout(notepadAutoSaveTimer);
    notepadDisconnectWs(true);
    notepadSetEditingEnabled(false);
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
    notepadIsDirty = true;
    document.body.classList.add('notepad-dirty');
    notepadScheduleAutoSave();
});

// Auto-save on title input
notepadTitleInput.addEventListener('input', () => {
    notepadIsDirty = true;
    document.body.classList.add('notepad-dirty');
    notepadScheduleAutoSave();
});

function notepadScheduleAutoSave() {
    if (!notepadInitDone) return;
    notepadSetStatus('unsaved');
    clearTimeout(notepadAutoSaveTimer);
    notepadAutoSaveTimer = setTimeout(notepadSave, notepadGetDelay());
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

    notepadRefreshList();
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
    const keyResp = await sendCustomRequest('NOTE', SERVER_URL + '/notes/key');
    const keyText = await keyResp.text();
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

    const exchangeResp = await sendCustomRequest('NOTE', SERVER_URL + '/notes/exchange',
        JSON.stringify({ clientPublicKey: clientPubB64 }),
        { 'Content-Type': 'application/json' }
    );
    const exchangeText = await exchangeResp.text();
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
            notepadHandleWsMessage(msg);
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
        notepadWs.send(JSON.stringify(msg));
    }
}

function notepadHandleWsMessage(msg) {
    if (msg.type === 'saved') {
        if (msg.success) {
            if (!notepadCurrentId) notepadCurrentId = msg.id;
            notepadDeleteBtnEl.disabled = false;
            notepadSetStatus('saved');
            notepadIsDirty = false;
            document.body.classList.remove('notepad-dirty');
            notepadRefreshList();
        } else {
            notepadSetStatus('error');
        }
    } else if (msg.type === 'loaded') {
        notepadHandleLoadResult(msg);
    } else if (msg.type === 'list') {
        notepadRenderList(msg.notes || []);
    } else if (msg.type === 'deleted') {
        notepadNewNote();
    } else if (msg.type === 'error') {
        console.error('[Notepad WS] Server error:', msg.error);
        notepadSetStatus('error');
    }
}

// ── CRUD operations ─────────────────────────────────────

async function notepadSave() {
    if (!notepadAvailable || !notepadDerivedKey) {
        notepadSetStatus('sessionFailed');
        return;
    }
    const text = notepadTextarea.value;
    const title = notepadTitleInput.value.trim() || t('notepadUntitled');

    if (!text && !notepadCurrentId) return;

    notepadSetStatus('saving');

    try {
        const encrypted = await notepadEncrypt(text);
        const dataB64 = uint8ToBase64(encrypted);

        if (notepadGetTransport() === 'ws' && notepadWs && notepadWs.readyState === WebSocket.OPEN) {
            // WebSocket save
            notepadSendWs({
                type: 'save',
                sessionId: notepadSessionId || '',
                noteId: notepadCurrentId || '',
                title: title,
                data: dataB64,
            });
        } else {
            // HTTP save
            const payload = { title: title, data: dataB64 };
            if (notepadCurrentId) payload.id = notepadCurrentId;

            const headers = { 'Content-Type': 'application/json' };
            if (notepadSessionId) headers['X-Session-Id'] = notepadSessionId;

            const response = await sendCustomRequest('NOTE', SERVER_URL + '/notes', JSON.stringify(payload), headers);
            const respText = await response.text();
            const result = JSON.parse(respText);

            if (result.success) {
                if (!notepadCurrentId) notepadCurrentId = result.id;
                notepadDeleteBtnEl.disabled = false;
                notepadSetStatus('saved');
                notepadIsDirty = false;
                document.body.classList.remove('notepad-dirty');
                notepadRefreshList();
            } else {
                notepadSetStatus('error');
            }
        }
    } catch (e) {
        console.error('[Notepad] Save error:', e);
        notepadSetStatus('error');
    }
}

async function notepadRefreshList() {
    if (!notepadAvailable) return;
    if (notepadGetTransport() === 'ws' && notepadWs && notepadWs.readyState === WebSocket.OPEN) {
        notepadSendWs({ type: 'list' });
        return;
    }

    try {
        const response = await sendCustomRequest('NOTE', SERVER_URL + '/notes?list');
        const text = await response.text();
        const result = JSON.parse(text);
        notepadRenderList(result.notes || []);
    } catch (e) {
        console.error('[Notepad] List error:', e);
    }
}

function notepadRenderList(notes) {
    const listEl = document.getElementById('notepadNoteList');
    if (!notes || notes.length === 0) {
        listEl.innerHTML = '<div class="notepad-no-notes">' + esc(t('notepadNoNotes')) + '</div>';
        return;
    }

    listEl.innerHTML = notes.map(note => {
        const isActive = note.id === notepadCurrentId;
        const date = note.updated_at ? new Date(note.updated_at).toLocaleString() : '';
        return '<button type="button" class="note-item' + (isActive ? ' active' : '') + '" data-note-id="' + encodeURIComponent(note.id) + '"' +
            (isActive ? ' aria-current="true"' : '') + '>' +
            '<div class="note-item-title">' + esc(note.title || t('notepadUntitled')) + '</div>' +
            '<div class="note-item-date">' + esc(date) + '</div>' +
            '</button>';
    }).join('');
}

async function notepadLoadNote(id) {
    if (!notepadAvailable || !notepadDerivedKey) {
        notepadSetStatus('sessionFailed');
        return;
    }
    notepadSetStatus('loading');

    try {
        const response = await sendCustomRequest('NOTE', SERVER_URL + '/notes/' + id);
        const text = await response.text();
        const result = JSON.parse(text);

        if (response.status === 404) {
            notepadSetStatus('loadError');
            return;
        }

        await notepadHandleLoadResult(result);
    } catch (e) {
        console.error('[Notepad] Load error:', e);
        notepadSetStatus('loadError');
    }
}

async function notepadHandleLoadResult(result) {
    try {
        if (!notepadAvailable || !notepadDerivedKey) {
            notepadSetStatus('sessionFailed');
            return;
        }
        const encryptedBytes = base64ToUint8(result.data);
        const plaintext = await notepadDecrypt(encryptedBytes);

        notepadCurrentId = result.id;
        notepadTitleInput.value = result.title || '';
        notepadTextarea.value = plaintext;
        notepadCharCount.textContent = notepadFormatCharCount(plaintext.length);
        notepadDeleteBtnEl.disabled = false;
        notepadIsDirty = false;
        document.body.classList.remove('notepad-dirty');
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

function notepadNewNote() {
    notepadCurrentId = null;
    notepadTitleInput.value = '';
    notepadTextarea.value = '';
    notepadCharCount.textContent = notepadFormatCharCount(0);
    notepadDeleteBtnEl.disabled = true;
    notepadIsDirty = false;
    document.body.classList.remove('notepad-dirty');
    clearTimeout(notepadAutoSaveTimer);
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
            const response = await sendCustomRequest('NOTE', SERVER_URL + '/notes/' + notepadCurrentId + '?delete');
            const text = await response.text();
            let result = null;
            try {
                result = JSON.parse(text);
            } catch (error) {
                result = null;
            }

            if (response.ok && result && result.success) {
                notepadNewNote();
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
