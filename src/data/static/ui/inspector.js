// ===== Shared request/response inspector =====
const exchangePreviewLimit = 4096;
const exchangeHexPreviewLimit = 64;
const exchangeSecretKeys = new Set([
    'authorization',
    'cookie',
    'set-cookie',
    'x-session-id',
    'x-k',
    'k',
    'key',
    'sessionid',
    'session_id',
    'password',
    'token',
]);
const exchangeInspectorStates = new Map();
const exchangeAreaRawText = new Map();

function exchangeCurrentMode() {
    if (typeof requestPreviewMode === 'string' && requestPreviewMode) {
        return requestPreviewMode;
    }

    try {
        const storedMode = localStorage.getItem('requestPreviewMode');
        return storedMode === 'summary' ? 'summary' : 'raw';
    } catch (_error) {
        return 'raw';
    }
}

function isExchangeSecretKey(key) {
    return exchangeSecretKeys.has(String(key || '').toLowerCase());
}

function redactExchangeValue(value, key = '') {
    if (isExchangeSecretKey(key)) {
        return `[${t('exchangeRedacted')}]`;
    }

    if (Array.isArray(value)) {
        return value.map(item => redactExchangeValue(item));
    }

    if (value && typeof value === 'object') {
        return Object.fromEntries(
            Object.entries(value).map(([entryKey, entryValue]) => [
                entryKey,
                redactExchangeValue(entryValue, entryKey),
            ])
        );
    }

    return value;
}

function normalizeExchangeHeaders(headers = {}) {
    return Object.fromEntries(
        Object.entries(headers || {}).map(([key, value]) => [
            key,
            redactExchangeValue(value, key),
        ])
    );
}

function truncateExchangeText(text, limit = exchangePreviewLimit) {
    const normalized = String(text || '');
    if (normalized.length <= limit) {
        return normalized;
    }

    return `${normalized.slice(0, limit)}\n... ${t('exchangeTruncated')} (${normalized.length - limit})`;
}

function formatExchangeHeaders(headers = {}) {
    const safeHeaders = normalizeExchangeHeaders(headers);
    const lines = Object.entries(safeHeaders)
        .filter(([, value]) => value !== undefined && value !== null && value !== '')
        .map(([key, value]) => `${key}: ${value}`);
    return lines.length ? lines.join('\n') : t('headersNA');
}

function formatExchangeBytes(bytes, limit = exchangeHexPreviewLimit) {
    if (!bytes) {
        return '';
    }

    const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    return Array.from(view.slice(0, limit))
        .map(value => value.toString(16).padStart(2, '0'))
        .join(' ');
}

function createExchangeTextBody(text, options = {}) {
    return {
        kind: options.kind || 'text',
        text: String(text || ''),
        contentType: options.contentType || '',
        size: options.size,
        label: options.label || '',
    };
}

function createExchangeJsonBody(value, options = {}) {
    return {
        kind: 'json',
        value,
        rawText: options.rawText,
        contentType: options.contentType || 'application/json',
        label: options.label || '',
    };
}

function createExchangeBinaryBody(options = {}) {
    return {
        kind: 'binary',
        filename: options.filename || '',
        contentType: options.contentType || 'application/octet-stream',
        size: Number(options.size || 0),
        bytes: options.bytes || null,
        label: options.label || '',
    };
}

function createExchangePreviewBody(options = {}) {
    return {
        kind: options.kind || 'preview',
        label: options.label || '',
        text: String(options.text || ''),
        size: options.size,
        contentType: options.contentType || '',
    };
}

function formatExchangeBody(body, options = {}) {
    if (!body) {
        return t('requestPreviewNoBody');
    }

    if (body.kind === 'json') {
        if (options.raw && body.rawText !== undefined) {
            return truncateExchangeText(body.rawText) || t('requestPreviewNoBody');
        }
        return truncateExchangeText(JSON.stringify(redactExchangeValue(body.value), null, 2));
    }

    if (body.kind === 'binary') {
        const lines = [
            `${t('exchangeBodyKind')}: ${t('exchangeBinaryBody')}`,
        ];
        if (body.filename) lines.push(`${t('fileName')}: ${body.filename}`);
        if (body.contentType) lines.push(`${t('responseSummaryFieldContentType')}: ${body.contentType}`);
        lines.push(`${t('requestPreviewFieldBodySize')}: ${formatSize(body.size || 0)}`);
        const hex = formatExchangeBytes(body.bytes);
        lines.push(`${t('exchangeHexPreview')}: ${hex || t('headersNA')}`);
        if ((body.size || 0) > exchangeHexPreviewLimit) {
            lines.push(`... ${t('exchangeTruncated')} (${body.size - exchangeHexPreviewLimit})`);
        }
        return lines.join('\n');
    }

    if (body.kind === 'preview') {
        const lines = [];
        if (body.label) lines.push(`${t('exchangeBodyKind')}: ${body.label}`);
        if (body.contentType) lines.push(`${t('responseSummaryFieldContentType')}: ${body.contentType}`);
        if (body.size !== undefined) lines.push(`${t('requestPreviewFieldBodySize')}: ${formatSize(body.size)}`);
        if (body.text) lines.push(truncateExchangeText(body.text));
        return lines.length ? lines.join('\n') : t('requestPreviewNoBody');
    }

    let text = body.text || '';
    if (!options.raw && body.contentType && body.contentType.includes('json')) {
        const parsed = parseJsonSafe(text);
        if (parsed !== null) {
            text = JSON.stringify(redactExchangeValue(parsed), null, 2);
        }
    }
    return truncateExchangeText(text) || t('requestPreviewNoBody');
}

function buildExchangeStartLine(message, side) {
    if (message.startLine) {
        return message.startLine;
    }

    if (message.transport === 'ws') {
        const direction = side === 'request' ? t('exchangeWsSend') : t('exchangeWsReceive');
        return `${direction} ${message.path || '/notes/ws'}`;
    }

    if (side === 'response') {
        const status = message.status ? `${message.status} ${message.statusText || ''}`.trim() : t('statusPending');
        return message.transport === 'ws' ? status : `HTTP/1.1 ${status}`;
    }

    const method = message.method || 'GET';
    const path = message.path || '/';
    return `${method} ${path} HTTP/1.1`;
}

function buildExchangeRawMessage(message = {}, side = 'request') {
    if (!message || message.phase === 'empty') {
        return message?.emptyText || t(side === 'request' ? 'exchangeRequestEmpty' : 'exchangeResponseEmpty');
    }

    if (message.rawText) {
        return message.rawText;
    }

    const lines = [buildExchangeStartLine(message, side)];
    const headersText = formatExchangeHeaders(message.headers || {});
    if (headersText && headersText !== t('headersNA')) {
        lines.push(headersText);
    }

    if (message.body) {
        const bodyText = formatExchangeBody(message.body, { raw: true });
        lines.push('', bodyText);
    }
    return lines.join('\n');
}

function buildExchangeMetric(label, value, options = {}) {
    if (value === undefined || value === null || value === '') {
        return '';
    }

    const classes = ['request-preview-summary__metric-value'];
    if (options.badge) classes.push('request-preview-summary__metric-value--badge');
    if (options.tone) classes.push(`request-preview-summary__metric-value--${options.tone}`);

    return `
        <div class="request-preview-summary__metric">
            <span class="request-preview-summary__metric-label">${esc(label)}</span>
            <span class="${classes.join(' ')}">${esc(value)}</span>
        </div>
    `;
}

function buildExchangeSummary(message = {}, side = 'request') {
    const metrics = [
        buildExchangeMetric(t('exchangeTransport'), message.transport === 'ws' ? 'WebSocket' : 'HTTP'),
        buildExchangeMetric(t('requestPreviewFieldMethod'), message.method || message.type || ''),
        buildExchangeMetric(t('requestPreviewFieldPath'), message.path || ''),
    ];

    if (side === 'response') {
        const statusValue = message.status
            ? formatHttpStatusLabel(message.status, message.statusText || '')
            : (message.phase === 'error' ? t('error') : t('statusPending'));
        metrics.push(buildExchangeMetric(
            t('responseSummaryFieldStatus'),
            statusValue,
            { badge: true, tone: message.phase === 'error' || message.status >= 400 ? 'danger' : (message.status ? 'success' : 'pending') }
        ));
    }

    if (message.duration) {
        metrics.push(buildExchangeMetric(t('time'), `${message.duration}ms`));
    }

    const headersText = formatExchangeHeaders(message.headers || {});
    const bodyText = formatExchangeBody(message.body, { raw: false });
    return `
        <div class="request-preview-summary exchange-summary">
            <div class="request-preview-summary__metrics">
                ${metrics.join('')}
            </div>
            ${headersText && headersText !== t('headersNA') ? buildSummarySection(t('headers'), headersText) : ''}
            ${buildSummarySection(side === 'request' ? t('requestBody') : t('responseBody'), bodyText, 'body')}
        </div>
    `;
}

function renderExchangePane(area, message = {}, side = 'request') {
    if (!area) {
        return;
    }

    const phase = message.phase || 'ready';
    const rawText = buildExchangeRawMessage(message, side);
    exchangeAreaRawText.set(area.id, rawText);
    area.dataset.exchangePhase = phase;
    area.dataset.exchangeTransport = message.transport || 'http';
    area.dataset.exchangeMethod = message.method || message.type || '';
    area.dataset.exchangePath = message.path || '';
    area.dataset.requestView = exchangeCurrentMode();

    if (phase === 'empty' || phase === 'sending') {
        area.textContent = rawText;
    } else if (exchangeCurrentMode() === 'summary') {
        area.innerHTML = buildExchangeSummary(message, side);
    } else {
        area.textContent = rawText;
    }
}

function renderExchangeInspector(scope) {
    const state = exchangeInspectorStates.get(scope);
    const root = document.querySelector(`[data-exchange-scope="${scope}"]`);
    if (!root || !state) {
        return;
    }

    renderExchangePane(root.querySelector('[data-exchange-pane="request"]'), state.request, 'request');
    renderExchangePane(root.querySelector('[data-exchange-pane="response"]'), state.response, 'response');
    root.dataset.exchangePhase = state.phase || state.response?.phase || state.request?.phase || 'ready';
}

function renderAllExchangeInspectors() {
    Array.from(exchangeInspectorStates.keys()).forEach(renderExchangeInspector);
}

function setExchangeInspector(scope, state = {}) {
    exchangeInspectorStates.set(scope, {
        phase: state.phase || state.response?.phase || state.request?.phase || 'ready',
        request: state.request || { phase: 'empty', emptyText: t('exchangeRequestEmpty') },
        response: state.response || { phase: 'empty', emptyText: t('exchangeResponseEmpty') },
    });
    renderExchangeInspector(scope);
}

function getExchangeAreaRawText(areaId) {
    return exchangeAreaRawText.get(areaId) || document.getElementById(areaId)?.innerText || '';
}

async function copyExchangeAreaRaw(areaId, liveRegionId, messageKey) {
    const text = getExchangeAreaRawText(areaId);
    if (!text) return;

    try {
        await writeTextToClipboard(text, areaId);
        announceLiveRegion(liveRegionId, t(messageKey));
    } catch (error) {
        announceLiveRegion(liveRegionId, formatActionErrorMessage(t('clipboardCopyFailed'), error));
    }
}

document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-exchange-copy-area]');
    if (!button) return;

    const areaId = button.dataset.exchangeCopyArea;
    const liveRegionId = button.dataset.exchangeCopyLive || '';
    const messageKey = button.dataset.exchangeCopyMessage || 'exchangeCopied';
    void copyExchangeAreaRaw(areaId, liveRegionId, messageKey);
});
