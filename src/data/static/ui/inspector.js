// ===== Shared request/response inspector =====
const exchangePreviewLimit = 4096;
const exchangeHexPreviewLimit = 64;
const exchangeSecretKeys = new Set([
    'authorization',
    'cookie',
    'clientpublickey',
    'client_public_key',
    'd',
    'data',
    'publickey',
    'public_key',
    'set-cookie',
    'serverpublickey',
    'server_public_key',
    'x-session-id',
    'x-d',
    'x-k',
    'k',
    'key',
    'sessionid',
    'session_id',
    'password',
    'token',
]);
const exchangeSecretKeyPatterns = [
    /^x-d(?:-.+)?$/,
];
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
    const normalized = String(key || '').trim().toLowerCase();
    const compact = normalized.replace(/[-_\s]/g, '');
    return exchangeSecretKeys.has(normalized) ||
        exchangeSecretKeys.has(compact) ||
        exchangeSecretKeyPatterns.some(pattern => pattern.test(normalized));
}

function exchangeRedactedLabel() {
    return `[${t('exchangeRedacted')}]`;
}

function redactExchangeValue(value, key = '') {
    if (isExchangeSecretKey(key)) {
        return exchangeRedactedLabel();
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

function safeDecodeExchangeComponent(value) {
    try {
        return decodeURIComponent(String(value || '').replace(/\+/g, ' '));
    } catch (_error) {
        return String(value || '');
    }
}

function redactExchangeQueryString(query) {
    return String(query || '').split('&').map(part => {
        if (!part) {
            return part;
        }

        const equalsIndex = part.indexOf('=');
        const key = equalsIndex === -1 ? part : part.slice(0, equalsIndex);
        if (!isExchangeSecretKey(safeDecodeExchangeComponent(key))) {
            return part;
        }

        return equalsIndex === -1 ? key : `${key}=${exchangeRedactedLabel()}`;
    }).join('&');
}

function redactExchangePath(path) {
    const text = String(path || '');
    const hashIndex = text.indexOf('#');
    const pathAndQuery = hashIndex === -1 ? text : text.slice(0, hashIndex);
    const hash = hashIndex === -1 ? '' : text.slice(hashIndex);
    const queryIndex = pathAndQuery.indexOf('?');
    if (queryIndex === -1) {
        return text;
    }

    const basePath = pathAndQuery.slice(0, queryIndex);
    const query = pathAndQuery.slice(queryIndex + 1);
    return `${basePath}?${redactExchangeQueryString(query)}${hash}`;
}

function redactExchangeJsonText(text, options = {}) {
    const parsed = parseJsonSafe(text);
    if (parsed === null || typeof parsed !== 'object') {
        return null;
    }

    return JSON.stringify(redactExchangeValue(parsed), null, options.pretty ? 2 : 0);
}

function redactExchangeHeaderLine(line) {
    const match = String(line || '').match(/^([^:\r\n]+):(\s*)(.*)$/);
    if (!match || !isExchangeSecretKey(match[1])) {
        return line;
    }

    return `${match[1]}:${match[2]}${exchangeRedactedLabel()}`;
}

function redactExchangeRequestLine(line) {
    const match = String(line || '').match(/^([A-Z]+)\s+(\S+)(\s+HTTP\/[0-9.]+.*)?$/);
    if (!match) {
        return line;
    }

    return `${match[1]} ${redactExchangePath(match[2])}${match[3] || ''}`;
}

function looksLikeExchangeQueryString(text) {
    return /^[^=\s&]+=[^\s]*(?:&[^=\s&]+=[^\s]*)*$/.test(String(text || ''));
}

function redactExchangeLines(text) {
    return String(text || '').split('\n').map(line => {
        const headerSafeLine = redactExchangeHeaderLine(line);
        const requestSafeLine = redactExchangeRequestLine(headerSafeLine);
        return looksLikeExchangeQueryString(requestSafeLine)
            ? redactExchangeQueryString(requestSafeLine)
            : requestSafeLine;
    }).join('\n');
}

function redactExchangeText(text, options = {}) {
    const normalized = String(text || '');
    if (!normalized) {
        return '';
    }

    const contentType = String(options.contentType || '').toLowerCase();
    if (contentType.includes('json') || /^[\s\r\n]*[\[{]/.test(normalized)) {
        const redactedJson = redactExchangeJsonText(normalized, options);
        if (redactedJson !== null) {
            return redactedJson;
        }
    }

    const bodySeparatorMatch = normalized.match(/\r?\n\r?\n/);
    if (options.splitHttpBody !== false && bodySeparatorMatch && bodySeparatorMatch.index !== undefined) {
        const separatorStart = bodySeparatorMatch.index;
        const separator = bodySeparatorMatch[0];
        const head = normalized.slice(0, separatorStart);
        const body = normalized.slice(separatorStart + separator.length);
        return [
            redactExchangeLines(head),
            separator,
            redactExchangeText(body, { ...options, splitHttpBody: false }),
        ].join('');
    }

    return redactExchangeLines(normalized);
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
            return truncateExchangeText(redactExchangeText(body.rawText, { contentType: body.contentType })) || t('requestPreviewNoBody');
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
        if (body.text) lines.push(truncateExchangeText(redactExchangeText(body.text, { contentType: body.contentType })));
        return lines.length ? lines.join('\n') : t('requestPreviewNoBody');
    }

    const text = redactExchangeText(body.text || '', {
        contentType: body.contentType,
        pretty: !options.raw,
    });
    return truncateExchangeText(text) || t('requestPreviewNoBody');
}

function redactExchangeBodyModel(body) {
    if (!body || typeof body !== 'object') {
        return body;
    }

    if (body.kind === 'json') {
        return {
            ...body,
            value: redactExchangeValue(body.value),
            rawText: body.rawText === undefined
                ? body.rawText
                : redactExchangeText(body.rawText, { contentType: body.contentType }),
        };
    }

    if (body.kind === 'preview' || body.kind === 'text' || !body.kind) {
        return {
            ...body,
            text: redactExchangeText(body.text || '', { contentType: body.contentType }),
        };
    }

    return { ...body };
}

function redactExchangeMessageModel(message = {}) {
    if (!message || typeof message !== 'object') {
        return message;
    }

    return {
        ...message,
        path: message.path ? redactExchangePath(message.path) : message.path,
        startLine: message.startLine ? redactExchangeText(message.startLine) : message.startLine,
        rawText: message.rawText ? redactExchangeText(message.rawText) : message.rawText,
        headers: normalizeExchangeHeaders(message.headers || {}),
        body: redactExchangeBodyModel(message.body),
    };
}

function buildExchangeStartLine(message, side) {
    if (message.startLine) {
        return redactExchangeText(message.startLine);
    }

    if (message.transport === 'ws') {
        const direction = side === 'request' ? t('exchangeWsSend') : t('exchangeWsReceive');
        return `${direction} ${redactExchangePath(message.path || '/notes/ws')}`;
    }

    if (side === 'response') {
        const status = message.status ? `${message.status} ${message.statusText || ''}`.trim() : t('statusPending');
        return message.transport === 'ws' ? status : `HTTP/1.1 ${status}`;
    }

    const method = message.method || 'GET';
    const path = redactExchangePath(message.path || '/');
    return `${method} ${path} HTTP/1.1`;
}

function buildExchangeRawMessage(message = {}, side = 'request') {
    if (!message || message.phase === 'empty') {
        return message?.emptyText || t(side === 'request' ? 'exchangeRequestEmpty' : 'exchangeResponseEmpty');
    }

    if (message.rawText) {
        return redactExchangeText(message.rawText, {
            contentType: message.body?.contentType,
        });
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
        buildExchangeMetric(t('requestPreviewFieldPath'), redactExchangePath(message.path || '')),
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
    area.dataset.exchangePath = redactExchangePath(message.path || '');
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
    const request = redactExchangeMessageModel(
        state.request || { phase: 'empty', emptyText: t('exchangeRequestEmpty') }
    );
    const response = redactExchangeMessageModel(
        state.response || { phase: 'empty', emptyText: t('exchangeResponseEmpty') }
    );

    exchangeInspectorStates.set(scope, {
        phase: state.phase || response?.phase || request?.phase || 'ready',
        request,
        response,
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
