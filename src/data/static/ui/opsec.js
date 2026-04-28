// ===== Advanced Upload =====
let opsecFile = null;
const opsecFileInput = document.getElementById('opsecFileInput');
const opsecUploadBtn = document.getElementById('opsecUploadBtn');
const opsecDropZone = document.getElementById('opsecDropZone');
const opsecEncryptCheckbox = document.getElementById('opsecEncrypt');
const opsecPasswordInput = document.getElementById('opsecPassword');
const opsecRandomMethodBtn = document.getElementById('opsecRandomMethodBtn');
const opsecSelectionState = document.getElementById('opsecSelectionState');
const opsecTransportWarning = document.getElementById('opsecTransportWarning');

function bindDropZoneKeyboardTrigger(container, input) {
    container.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            input.click();
        }
    });
}

function getOpsecSelectionText() {
    if (!opsecFile) {
        return t('opsecSelectionIdle');
    }

    return `${t('selectedLabel')}: ${opsecFile.name} (${formatSize(opsecFile.size)})`;
}

function refreshOpsecSelectionLocale() {
    if (opsecSelectionState) {
        opsecSelectionState.hidden = !opsecFile;
        opsecSelectionState.textContent = getOpsecSelectionText();
    }

    if (opsecDropZone) {
        opsecDropZone.classList.toggle('has-selection', Boolean(opsecFile));
    }
}

function setOpsecFile(file) {
    opsecFile = file || null;
    opsecUploadBtn.disabled = !opsecFile;
    refreshOpsecSelectionLocale();

    if (opsecFile) {
        announceLiveRegion('opsecResponseAreaLive', `${t('opsecFileSelected')}: ${opsecFile.name}`);
        setExchangeInspector('opsec', {
            phase: 'ready',
            request: {
                phase: 'empty',
                emptyText: t('exchangeRequestEmpty'),
            },
            response: {
                phase: 'ready',
                startLine: `${t('opsecFileSelected')}: ${opsecFile.name}`,
                body: createExchangeTextBody(`${opsecFile.name} (${formatSize(opsecFile.size)})`),
            },
        });
    }

    checkOpsecTransportWarning();
}

if (opsecRandomMethodBtn) {
    opsecRandomMethodBtn.addEventListener('click', generateRandomMethod);
}

if (opsecUploadBtn) {
    opsecUploadBtn.addEventListener('click', opsecUpload);
}

// Toggle password field when encryption checkbox changes
opsecEncryptCheckbox.addEventListener('change', () => {
    opsecPasswordInput.disabled = !opsecEncryptCheckbox.checked;
    if (opsecEncryptCheckbox.checked) {
        opsecPasswordInput.focus();
    }
});

// Toggle base64 key checkbox when send key checkbox changes
const opsecSendKeyCheckbox = document.getElementById('opsecSendKey');
const opsecKeyBase64Checkbox = document.getElementById('opsecKeyBase64');
opsecSendKeyCheckbox.addEventListener('change', () => {
    opsecKeyBase64Checkbox.disabled = !opsecSendKeyCheckbox.checked;
    if (!opsecSendKeyCheckbox.checked) {
        opsecKeyBase64Checkbox.checked = false;
    }
});

// XOR encryption function - uses UTF-8 encoding for password (matches Python)
function xorEncrypt(data, password) {
    if (!password) return data;

    // Convert password to UTF-8 bytes (same as Python's .encode('utf-8'))
    const encoder = new TextEncoder();
    const keyBytes = encoder.encode(password);

    // XOR each byte with key
    const result = new Uint8Array(data.length);
    for (let i = 0; i < data.length; i++) {
        result[i] = data[i] ^ keyBytes[i % keyBytes.length];
    }
    return result;
}

// Random method names for advanced upload
const methodPrefixes = ['CHECK', 'SYNC', 'VERIFY', 'UPDATE', 'QUERY', 'REPORT', 'SUBMIT', 'VALIDATE', 'PROCESS', 'EXECUTE'];
const methodSuffixes = ['DATA', 'STATUS', 'INFO', 'CONTENT', 'RESOURCE', 'ITEM', 'OBJECT', 'RECORD', 'ENTRY', ''];

function generateRandomMethod() {
    const prefix = methodPrefixes[Math.floor(Math.random() * methodPrefixes.length)];
    const suffix = methodSuffixes[Math.floor(Math.random() * methodSuffixes.length)];
    const method = suffix ? `${prefix}${suffix}` : prefix;
    document.getElementById('opsecMethodInput').value = method;
}

// Инициализация случайным методом
generateRandomMethod();

// Transport size warning + auto-switch
function setOpsecTransport(value) {
    const radio = document.querySelector(`input[name="opsecTransport"][value="${value}"]`);
    if (radio) radio.checked = true;
}

function hideOpsecTransportWarning() {
    if (!opsecTransportWarning) {
        return;
    }

    opsecTransportWarning.hidden = true;
    delete opsecTransportWarning.dataset.fromKey;
    delete opsecTransportWarning.dataset.toKey;
}

function refreshOpsecTransportWarningLocale() {
    if (!opsecTransportWarning || opsecTransportWarning.hidden) {
        return;
    }

    const fromKey = opsecTransportWarning.dataset.fromKey;
    const toKey = opsecTransportWarning.dataset.toKey;
    if (!fromKey || !toKey) {
        return;
    }

    opsecTransportWarning.textContent = t('opsecTransportAutoSwitch')
        .replace('{0}', t(toKey))
        .replace('{1}', t(fromKey));
}

function showOpsecTransportWarning(fromKey, toKey) {
    if (!opsecTransportWarning) {
        return;
    }

    opsecTransportWarning.dataset.fromKey = fromKey;
    opsecTransportWarning.dataset.toKey = toKey;
    opsecTransportWarning.hidden = false;
    refreshOpsecTransportWarningLocale();
}

function checkOpsecTransportWarning() {
    const transport = document.querySelector('input[name="opsecTransport"]:checked')?.value || 'body';
    if (!opsecFile || transport === 'body') {
        hideOpsecTransportWarning();
        return;
    }
    // base64 inflates size by ~33%
    const b64Size = Math.ceil(opsecFile.size * 4 / 3);

    if (transport === 'url' && b64Size > 1500) {
        // Auto-switch: URL → Headers (or Body if too large for headers too)
        if (b64Size > 24000) {
            setOpsecTransport('body');
            showOpsecTransportWarning('opsecTransportUrl', 'opsecTransportBody');
        } else {
            setOpsecTransport('headers');
            showOpsecTransportWarning('opsecTransportUrl', 'opsecTransportHeaders');
        }
    } else if (transport === 'headers' && b64Size > 24000) {
        // Auto-switch: Headers → Body
        setOpsecTransport('body');
        showOpsecTransportWarning('opsecTransportHeaders', 'opsecTransportBody');
    } else {
        hideOpsecTransportWarning();
    }
}

document.querySelectorAll('input[name="opsecTransport"]').forEach(r => {
    r.addEventListener('change', checkOpsecTransportWarning);
});

opsecFileInput.addEventListener('change', () => {
    if (opsecFileInput.files.length > 0) {
        setOpsecFile(opsecFileInput.files[0]);
        opsecFileInput.value = '';
    }
});

bindDropZoneKeyboardTrigger(opsecDropZone, opsecFileInput);

opsecDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    opsecDropZone.classList.add('dragover');
});

opsecDropZone.addEventListener('dragleave', () => {
    opsecDropZone.classList.remove('dragover');
});

opsecDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    opsecDropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        setOpsecFile(e.dataTransfer.files[0]);
    }
});

async function opsecUpload() {
    if (!opsecFile) return;

    const method = document.getElementById('opsecMethodInput').value || 'CHECKDATA';
    const includeName = document.getElementById('opsecIncludeName').checked;
    const useEncryption = opsecEncryptCheckbox.checked;
    const password = opsecPasswordInput.value;
    const transport = document.querySelector('input[name="opsecTransport"]:checked')?.value || 'body';

    // Validate password if encryption is enabled
    if (useEncryption && !password) {
        announceLiveRegion('opsecResponseAreaLive', t('opsecPasswordRequired'));
        setExchangeInspector('opsec', {
            phase: 'error',
            request: {
                phase: 'empty',
                emptyText: t('exchangeRequestEmpty'),
            },
            response: {
                phase: 'error',
                startLine: t('opsecPasswordRequired'),
                body: createExchangeTextBody(t('opsecPasswordRequired')),
            },
        });
        return;
    }

    announceLiveRegion('opsecResponseAreaLive', `${t('opsecUploading')} ${method} [${transport}]`);
    setExchangeInspector('opsec', {
        phase: 'sending',
        request: {
            phase: 'empty',
            emptyText: t('exchangeRequestEmpty'),
        },
        response: {
            phase: 'sending',
            startLine: `${t('opsecUploading')} ${method} [${transport}]`,
            body: createExchangeTextBody(`${t('opsecUploading')} ${method}${useEncryption ? ' (' + t('opsecXorEncryption') + ')' : ''} [${transport}]...`),
        },
    });
    opsecUploadBtn.disabled = true;

    try {
        const arrayBuffer = await opsecFile.arrayBuffer();
        let dataBytes = new Uint8Array(arrayBuffer);

        // Apply XOR encryption if enabled
        if (useEncryption) {
            dataBytes = xorEncrypt(dataBytes, password);
            console.log(`[Advanced upload] XOR encryption applied with password length: ${password.length}`);
        }

        let binary = '';
        const chunkSize = 8192;
        for (let i = 0; i < dataBytes.length; i += chunkSize) {
            binary += String.fromCharCode.apply(null, dataBytes.subarray(i, i + chunkSize));
        }
        const base64Std = btoa(binary);

        // Build payload fields
        const sendKeyToServer = document.getElementById('opsecSendKey').checked;
        const encodeKeyBase64 = document.getElementById('opsecKeyBase64').checked;
        const fields = { d: base64Std };
        if (useEncryption) {
            fields.e = 'xor';
            if (sendKeyToServer) {
                if (encodeKeyBase64) {
                    fields.k = btoa(unescape(encodeURIComponent(password)));
                    fields.kb64 = 'true';
                } else {
                    fields.k = password;
                }
            }
        }
        if (includeName) {
            fields.n = opsecFile.name;
        }

        // Random path (does not contain filename!)
        const randomPath = '/' + Math.random().toString(36).substring(2, 10);
        let requestUrl = SERVER_URL + randomPath;
        let requestBody = null;
        let requestHeaders = {};
        let response;
        let requestPath = randomPath;
        let requestBodyDescriptor = null;

        console.log(`[Advanced upload] Method: ${method}, Path: ${randomPath}, Transport: ${transport}, Include name: ${includeName}`);

        if (transport === 'headers') {
            // Send data in HTTP headers — chunked if > 7000 chars
            const HEADER_CHUNK_SIZE = 7000;
            if (base64Std.length > HEADER_CHUNK_SIZE) {
                for (let i = 0, idx = 0; i < base64Std.length; i += HEADER_CHUNK_SIZE, idx++) {
                    requestHeaders[`X-D-${idx}`] = base64Std.substring(i, i + HEADER_CHUNK_SIZE);
                }
            } else {
                requestHeaders['X-D'] = base64Std;
            }
            if (fields.e) requestHeaders['X-E'] = fields.e;
            if (fields.k) requestHeaders['X-K'] = fields.k;
            if (fields.kb64) requestHeaders['X-Kb64'] = fields.kb64;
            if (fields.n) requestHeaders['X-N'] = fields.n;
            if (fields.h) requestHeaders['X-H'] = fields.h;
            requestBodyDescriptor = createExchangePreviewBody({
                label: t('opsecTransportHeaders'),
                size: base64Std.length,
                text: Object.entries(requestHeaders).map(([key, value]) => `${key}: ${value}`).join('\n'),
            });
            setExchangeInspector('opsec', {
                phase: 'sending',
                request: {
                    transport: 'http',
                    method,
                    path: requestPath,
                    headers: requestHeaders,
                    body: requestBodyDescriptor,
                },
                response: {
                    phase: 'sending',
                    startLine: `${t('opsecUploading')} ${method} [${transport}]`,
                    body: createExchangeTextBody(t('statusPending')),
                },
            });
            response = await sendCustomRequest(method, requestUrl, null, requestHeaders);
        } else if (transport === 'url') {
            // Send data in URL query parameters with URL-safe base64
            const urlSafeB64 = base64Std.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
            const params = new URLSearchParams();
            params.set('d', urlSafeB64);
            if (fields.e) params.set('e', fields.e);
            if (fields.k) params.set('k', fields.k);
            if (fields.kb64) params.set('kb64', fields.kb64);
            if (fields.n) params.set('n', fields.n);
            if (fields.h) params.set('h', fields.h);
            requestUrl += '?' + params.toString();
            requestPath = randomPath + '?' + params.toString();
            requestBodyDescriptor = createExchangePreviewBody({
                label: t('opsecTransportUrl'),
                size: params.toString().length,
                text: params.toString(),
            });
            setExchangeInspector('opsec', {
                phase: 'sending',
                request: {
                    transport: 'http',
                    method,
                    path: requestPath,
                    headers: {},
                    body: requestBodyDescriptor,
                },
                response: {
                    phase: 'sending',
                    startLine: `${t('opsecUploading')} ${method} [${transport}]`,
                    body: createExchangeTextBody(t('statusPending')),
                },
            });
            response = await sendCustomRequest(method, requestUrl, null, {});
        } else {
            // Default: send as JSON body
            const payload = { d: fields.d };
            if (fields.e) payload.e = fields.e;
            if (fields.k) payload.k = fields.k;
            if (fields.kb64) payload.kb64 = true;
            if (fields.n) payload.n = fields.n;
            requestHeaders['Content-Type'] = 'application/json';
            requestBody = JSON.stringify(payload);
            requestBodyDescriptor = createExchangeTextBody(requestBody, { contentType: 'application/json' });
            setExchangeInspector('opsec', {
                phase: 'sending',
                request: {
                    transport: 'http',
                    method,
                    path: requestPath,
                    headers: requestHeaders,
                    body: requestBodyDescriptor,
                },
                response: {
                    phase: 'sending',
                    startLine: `${t('opsecUploading')} ${method} [${transport}]`,
                    body: createExchangeTextBody(t('statusPending')),
                },
            });
            response = await sendCustomRequest(method, requestUrl, requestBody, requestHeaders);
        }

        const text = await response.text();
        console.log(`[Advanced upload] Response:`, text);

        let result;
        try {
            result = JSON.parse(text);
        } catch (e) {
            result = { ok: false, error: text };
        }

        if (result.ok) {
            const responseSummary = `--- ${t('opsecSuccess')} ---
${t('opsecId')}: ${result.id}
${t('opsecSize')}: ${result.sz} ${t('opsecBytes')}
${t('opsecTransportUsed')}: ${result.transport || transport}

${t('methodLabel')} ${method} ${t('opsecMethodRandom')}
Path: ${randomPath} ${t('opsecPathNoName')}
${t('opsecNameInReq')}: ${includeName ? t('opsecYes') : t('opsecNoHidden')}
${t('opsecEncryption')}: ${useEncryption ? (sendKeyToServer ? t('opsecXorDecrypted') + (encodeKeyBase64 ? t('opsecKeyInBase64') : '') + ')' : t('opsecXorEncrypted')) : t('opsecNone')}`;
            setExchangeInspector('opsec', {
                phase: 'complete',
                request: {
                    transport: 'http',
                    method,
                    path: requestPath,
                    headers: requestHeaders,
                    body: requestBodyDescriptor,
                },
                response: {
                    transport: 'http',
                    method,
                    path: randomPath,
                    phase: 'complete',
                    status: response.status,
                    statusText: response.statusText || t('opsecUploaded'),
                    headers: response.headers,
                    body: createExchangeTextBody(responseSummary, { contentType: 'text/plain' }),
                },
            });
            announceLiveRegion('opsecResponseAreaLive', `${t('opsecSuccess')}: ${result.id}`);
            // Generate new random method for next upload
            generateRandomMethod();
        } else {
            announceLiveRegion('opsecResponseAreaLive', `${method} ${t('error')}: ${result.error || 'Unknown error'}`);
            setExchangeInspector('opsec', {
                phase: 'error',
                request: {
                    transport: 'http',
                    method,
                    path: requestPath,
                    headers: requestHeaders,
                    body: requestBodyDescriptor,
                },
                response: {
                    transport: 'http',
                    method,
                    path: randomPath,
                    phase: 'error',
                    status: response.status,
                    statusText: response.statusText || t('error'),
                    headers: response.headers,
                    body: createExchangeTextBody(result.error || 'Unknown error'),
                },
            });
        }
    } catch (error) {
        console.error('[Advanced upload] Error:', error);
        announceLiveRegion('opsecResponseAreaLive', `${t('error')}: ${error.message}`);
        setExchangeInspector('opsec', {
            phase: 'error',
            request: {
                phase: 'empty',
                emptyText: t('exchangeRequestEmpty'),
            },
            response: {
                phase: 'error',
                startLine: t('error'),
                body: createExchangeTextBody(error.message),
            },
        });
    }

    opsecUploadBtn.disabled = false;
}

refreshOpsecSelectionLocale();
